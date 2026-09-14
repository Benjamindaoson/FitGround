## 1. Document the P0 data foundation

- [ ] Create a data-foundation document that names the source roles, exact non-goals, model/pipeline ceiling, storage layout, and GPU admission gates.
- [ ] Update the README's existing-assets section without changing legacy claims or readiness status.

## 2. Acquire source code reproducibly

- [x] Resolve the upstream HEAD for FitVTON and GarmentCode before acquisition.
- [x] Acquire each fixed commit as a GitHub source archive after shallow Git transport stalled before a readable HEAD; validate the archive and extract only into new documented directories.
- [x] Record the fixed commit and archive SHA-256; no credential-bearing remote is created by archive acquisition.

## 3. Acquire the two approved public datasets

- [ ] Download GarmentCodeVTONDataset at `f51b54db869fc4b1a7f32b017cdbfa80cb22956a` into an empty local directory using the installed Hugging Face client; download remains in progress and is resumable.
- [x] Download FittingEffectDataset at `a1de636764dd7ce848737752e918ab3eec02ff03` into an empty local directory using the installed Hugging Face client.
- [x] Do not pass a token or persist a credential; preserve client download metadata for resume.

## 4. Verify and receipt

- [ ] Count GarmentCodeVTONDataset regular local files and byte totals after its acquisition completes.
- [x] Write a machine-readable receipt with expected versus observed totals and the public source revisions; its overall status remains `IN_PROGRESS` until the GCVTON total matches.
- [x] Run project tests; report any tests unrelated to this data-only change separately.
