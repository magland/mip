# Platform Tags for .mhl Packages

## Package Naming Convention

MHL packages follow this naming format:

```
{package}-{version}-{matlab_tag}-{abi_tag}-{platform_tag}.mhl
```

Example: `fmm2d-1.0.0-any-none-linux_x86_64.mhl`

## Platform Tag Reference

### Platform-Independent

- `any` - Either pure MATLAB code with no compiled components, OR includes compiled binaries for all supported platforms

### Linux

- `linux_x86_64` - 64-bit Intel/AMD Linux
- `linux_aarch64` - 64-bit ARM Linux (e.g., Raspberry Pi 64-bit, AWS Graviton)
- `linux_i686` - 32-bit Intel/AMD Linux (legacy)

### macOS

- `macosx_10_9_x86_64` - Intel Mac, compatible with macOS 10.9+
- `macosx_11_0_arm64` - Apple Silicon (M1/M2/M3), compatible with macOS 11+
- `macosx_10_9_universal2` - Universal binary supporting both Intel and Apple Silicon

### Windows

- `win_amd64` - 64-bit Windows
- `win32` - 32-bit Windows
- `win_arm64` - ARM64 Windows (Surface Pro X, etc.)

## Notes

- The `matlab_tag` is typically `any` (not version-specific)
- The `abi_tag` is typically `none` (no specific MATLAB ABI requirement)
- Packages with compiled MEX files must specify the target platform, unless they contain binaries for all platforms
- Pure MATLAB packages should use platform tag `any` for maximum compatibility
