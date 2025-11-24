function unimport(packageName)
    % unimport - Unimport a mip package from MATLAB path
    %
    % Usage:
    %   mip.unimport('packageName')
    %
    % This function unimports the specified package by executing its 
    % unsetup.m file (if it exists) and then prunes any packages that
    % are no longer needed (packages that were imported as dependencies
    % but are not dependencies of any directly imported package).
    
    global MIP_IMPORTED_PACKAGES;
    global MIP_DIRECTLY_IMPORTED_PACKAGES;
    
    % Check if package is imported
    if ~isPackageImported(packageName)
        fprintf('Package "%s" is not currently imported\n', packageName);
        return;
    end
    
    % Get the mip packages directory
    importFileDir = fileparts(mfilename('fullpath'));
    mipRootDir = fileparts(fileparts(importFileDir));
    packagesDir = fullfile(mipRootDir, 'packages');
    packageDir = fullfile(packagesDir, packageName);
    
    % Execute unsetup.m if it exists
    executeUnsetup(packageDir, packageName);
    
    % Remove from directly imported packages
    if ~isempty(MIP_DIRECTLY_IMPORTED_PACKAGES)
        MIP_DIRECTLY_IMPORTED_PACKAGES = MIP_DIRECTLY_IMPORTED_PACKAGES(...
            ~strcmp(MIP_DIRECTLY_IMPORTED_PACKAGES, packageName));
    end
    
    % Remove from imported packages
    if ~isempty(MIP_IMPORTED_PACKAGES)
        MIP_IMPORTED_PACKAGES = MIP_IMPORTED_PACKAGES(...
            ~strcmp(MIP_IMPORTED_PACKAGES, packageName));
    end
    
    fprintf('Unimported package "%s"\n', packageName);
    
    % Prune packages that are no longer needed
    pruneUnusedPackages(packagesDir);
end

function executeUnsetup(packageDir, packageName)
    % Execute unsetup.m for a package if it exists
    unsetupFile = fullfile(packageDir, 'unsetup.m');
    
    if ~exist(unsetupFile, 'file')
        warning('mip:unsetupNotFound', ...
                'Package "%s" does not have an unsetup.m file. Path changes may persist.', ...
                packageName);
        return;
    end
    
    % Execute the unsetup.m file
    originalDir = pwd;
    cd(packageDir);
    try
        run(unsetupFile);
    catch ME
        warning('mip:unsetupError', ...
                'Error executing unsetup.m for package "%s": %s', ...
                packageName, ME.message);
    end
    cd(originalDir);
end

function pruneUnusedPackages(packagesDir)
    % Prune packages that are no longer needed
    % A package is needed if it is:
    % 1. Directly imported by the user, OR
    % 2. A dependency of a directly imported package
    
    global MIP_IMPORTED_PACKAGES;
    global MIP_DIRECTLY_IMPORTED_PACKAGES;
    
    if isempty(MIP_IMPORTED_PACKAGES)
        return;
    end
    
    if isempty(MIP_DIRECTLY_IMPORTED_PACKAGES)
        MIP_DIRECTLY_IMPORTED_PACKAGES = {};
    end
    
    % Build set of all needed packages (directly imported + their dependencies)
    neededPackages = {};
    for i = 1:length(MIP_DIRECTLY_IMPORTED_PACKAGES)
        directPkg = MIP_DIRECTLY_IMPORTED_PACKAGES{i};
        neededPackages = [neededPackages, getAllDependencies(directPkg, packagesDir)];
    end
    
    % Add directly imported packages themselves
    neededPackages = unique([MIP_DIRECTLY_IMPORTED_PACKAGES, neededPackages]);
    
    % Find packages to prune (imported but not needed)
    packagesToPrune = {};
    for i = 1:length(MIP_IMPORTED_PACKAGES)
        pkg = MIP_IMPORTED_PACKAGES{i};
        if ~ismember(pkg, neededPackages)
            packagesToPrune{end+1} = pkg;
        end
    end
    
    % Prune each unnecessary package
    if ~isempty(packagesToPrune)
        fprintf('Pruning unnecessary packages: %s\n', strjoin(packagesToPrune, ', '));
        for i = 1:length(packagesToPrune)
            pkg = packagesToPrune{i};
            packageDir = fullfile(packagesDir, pkg);
            
            % Execute unsetup.m
            executeUnsetup(packageDir, pkg);
            
            % Remove from imported packages
            MIP_IMPORTED_PACKAGES = MIP_IMPORTED_PACKAGES(...
                ~strcmp(MIP_IMPORTED_PACKAGES, pkg));
            
            fprintf('  Pruned package "%s"\n', pkg);
        end
    end
end

function deps = getAllDependencies(packageName, packagesDir)
    % Recursively get all dependencies of a package
    deps = {};
    
    packageDir = fullfile(packagesDir, packageName);
    mipJsonPath = fullfile(packageDir, 'mip.json');
    
    if ~exist(mipJsonPath, 'file')
        return;
    end
    
    try
        % Read and parse mip.json
        fid = fopen(mipJsonPath, 'r');
        jsonText = fread(fid, '*char')';
        fclose(fid);
        mipConfig = jsondecode(jsonText);
        
        % Get direct dependencies
        if isfield(mipConfig, 'dependencies') && ~isempty(mipConfig.dependencies)
            for i = 1:length(mipConfig.dependencies)
                dep = mipConfig.dependencies{i};
                if ~ismember(dep, deps)
                    deps{end+1} = dep;
                    % Recursively get dependencies of this dependency
                    transitiveDeps = getAllDependencies(dep, packagesDir);
                    deps = unique([deps, transitiveDeps]);
                end
            end
        end
    catch ME
        warning('mip:jsonParseError', ...
                'Could not parse mip.json for package "%s": %s', ...
                packageName, ME.message);
    end
end

function imported = isPackageImported(packageName)
    % Helper function to check if a package has already been imported
    global MIP_IMPORTED_PACKAGES;
    if isempty(MIP_IMPORTED_PACKAGES)
        MIP_IMPORTED_PACKAGES = {};
    end
    imported = ismember(packageName, MIP_IMPORTED_PACKAGES);
end
