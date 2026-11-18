# Export and compilation of classical and vision models

State from a search on 2026-10-17; the vendors' documentation was not opened (secondary sources and abstracts), so check the versions
and flags in the documentation of the installed version.

## Order
1. The baseline measurement and the profile (SKILL.md, step 1).
2. The cheapest: `torch.compile`, a smaller resolution or a batch matched to the hardware, FP16/BF16.
3. Export to ONNX → the target engine (ONNX Runtime, OpenVINO, TensorRT).
4. INT8 quantization with calibration on representative images or production data.
5. Numerical parity (a tolerance on the outputs, the task metric) and a measurement on the target hardware.

## Tools
- **ONNX:** `torch.onnx.export`; since PyTorch 2.9 the path based on `torch.export` (`dynamo=True`) is the default, the old TorchScript path
  requires `dynamo=False` and is being phased out (release notes 2.9, search). Use `dynamic_shapes` instead of `dynamic_axes`.
  The new path can reveal graph capture errors that were hidden before.
- **TensorRT** (NVIDIA GPU): an engine built from ONNX (`trtexec` or the API), by default tied to the GPU architecture and the TensorRT version;
  the version and hardware compatibility modes are exceptions, and rebuild INT8 calibration tables after a version change (support matrix 10.8,
  DRIVE OS guide). Build on the GPU type on which production runs.
- **OpenVINO + NNCF** (Intel CPU and GPU): `nncf.quantize()` to INT8; release 2026.0 removed `create_compressed_model()`
  and some experimental methods (release notes). Recommended inputs: OpenVINO IR, PyTorch, ONNX. Accuracy control
  (`quantize_with_accuracy_control`) — status in 2026 not confirmed [unverified].
- **torch.compile:** modes `default`, `reduce-overhead` (CUDA graphs, less overhead on small batches, more memory),
  `max-autotune` (longer compilation, faster code); the first call is slow (compilation), so measure after a warm-up.
  Graph breaks reduce the gain — check them before tuning the modes.

## Traps
- Dynamic sizes: an export with a fixed shape inflates the speed and breaks other sizes.
- Pre- and post-processing (image scaling, NMS) usually stays outside the engine and can be a bottleneck.
- Numerical differences after INT8 grow in the tail of the distribution: check the worst cases, not only the average.
- A TensorRT engine is not a portable artifact; keep ONNX and the build script in the repository, not the engine file as the only copy.
