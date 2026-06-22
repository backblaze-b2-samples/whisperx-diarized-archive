"""Single-sourced torch `weights_only` allowlist for pyannote checkpoints.

torch 2.6+ flipped `torch.load`'s default to `weights_only=True`. Both load
paths in this engine hit that flip:

* transcription (`transcribe.py`) — `whisperx.load_model(...)` eagerly loads
  whisperx's bundled pyannote VAD *segmentation* checkpoint via lightning's
  `pl_load` -> `torch.load`;
* diarization (`diarize.py`) — `DiarizationPipeline(...)` loads pyannote's
  gated `speaker-diarization-3.1` checkpoints the same way.

Neither library passes `weights_only=False`, so the safe unpickler rejects the
non-tensor classes (omegaconf configs, pyannote task specs, stdlib containers)
baked into those checkpoints. We can't downgrade torch below the flip
(whisperx 3.7.9 pins torch~=2.8.0), so — as pyannote's own error message
recommends — we allowlist exactly the globals the checkpoints need instead of
blanket-disabling `weights_only`.

`torch.serialization.add_safe_globals(...)` is process-global and idempotent,
so a single application before the first load (transcription always runs first)
covers both paths. We hoist it here so the list is single-sourced (AGENTS.md
DRY rule: extract when used in 2+ places). The exact set was discovered
empirically — torch names one missing global at a time — against the pinned
stack (whisperx 3.7.9, pyannote.audio 3.4.0, torch 2.8.0); the VAD and
diarization checkpoints share the same set.

Heavy imports stay lazy (inside the function) per the engine's lazy-import
invariant, so importing this module is free.
"""


def allowlist_pyannote_globals() -> None:
    """Allowlist the globals pyannote's checkpoints unpickle under torch 2.6+.

    Idempotent and process-global. Call before any `torch.load`-backed pyannote
    checkpoint load — `whisperx.load_model(...)` and `DiarizationPipeline(...)`.
    """
    import collections
    import typing

    import torch  # type: ignore
    from omegaconf.base import ContainerMetadata, Metadata  # type: ignore
    from omegaconf.listconfig import ListConfig  # type: ignore
    from omegaconf.nodes import AnyNode  # type: ignore
    from pyannote.audio.core.model import Introspection  # type: ignore
    from pyannote.audio.core.task import (  # type: ignore
        Problem,
        Resolution,
        Specifications,
    )

    torch.serialization.add_safe_globals(
        [
            # torch / pyannote task metadata
            torch.torch_version.TorchVersion,
            Specifications,
            Problem,
            Resolution,
            Introspection,
            # omegaconf-pickled hyperparameter configs
            ListConfig,
            ContainerMetadata,
            Metadata,
            AnyNode,
            # stdlib containers / scalars referenced by those configs
            typing.Any,
            collections.defaultdict,
            list,
            dict,
            int,
        ]
    )
