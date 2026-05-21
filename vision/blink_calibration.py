from dataclasses import dataclass


CALIBRATION_ACTION_STARTED = "CALIBRATION_STARTED"
CALIBRATION_ACTION_SAVED = "CALIBRATION_SAVED"
CALIBRATION_ACTION_FAILED = "CALIBRATION_FAILED"


@dataclass(frozen=True)
class BlinkCalibrationResult:
    success: bool
    closed_threshold: float | None
    open_average: float | None
    closed_average: float | None
    reason: str


class BlinkCalibrator:
    """Collects short open/closed eye samples and computes a blink threshold."""

    def __init__(
        self,
        sample_duration_ms: int = 2000,
        min_samples: int = 5,
    ) -> None:
        self.sample_duration_ms = sample_duration_ms
        self.min_samples = min_samples
        self._phase = "idle"
        self._phase_started_ms: int | None = None
        self._open_samples: list[float] = []
        self._closed_samples: list[float] = []
        self._status = "Calibration: idle"

    @property
    def running(self) -> bool:
        return self._phase in ("open", "closed")

    @property
    def status(self) -> str:
        return self._status

    def start(self, timestamp_ms: int) -> str:
        self._phase = "open"
        self._phase_started_ms = timestamp_ms
        self._open_samples = []
        self._closed_samples = []
        self._status = "Calibration: keep eyes open normally"
        return CALIBRATION_ACTION_STARTED

    def update(
        self,
        eye_open: float | None,
        timestamp_ms: int,
    ) -> BlinkCalibrationResult | None:
        if not self.running or self._phase_started_ms is None:
            return None

        if timestamp_ms - self._phase_started_ms >= self.sample_duration_ms:
            if self._phase == "open":
                if len(self._open_samples) < self.min_samples:
                    return self._fail("not enough open-eye samples")
                self._phase = "closed"
                self._phase_started_ms = timestamp_ms
                self._status = "Calibration: close eyes"
                return None

            return self._finish()

        if eye_open is not None:
            sample = float(eye_open)
            if self._phase == "open":
                self._open_samples.append(sample)
            elif self._phase == "closed":
                self._closed_samples.append(sample)

        return None

    def _finish(self) -> BlinkCalibrationResult:
        if len(self._closed_samples) < self.min_samples:
            return self._fail("not enough closed-eye samples")

        open_average = sum(self._open_samples) / len(self._open_samples)
        closed_average = sum(self._closed_samples) / len(self._closed_samples)
        if open_average <= closed_average:
            return self._fail(
                "open-eye average must be higher than closed-eye average",
                open_average=open_average,
                closed_average=closed_average,
            )

        closed_threshold = (open_average + closed_average) / 2
        self._phase = "idle"
        self._phase_started_ms = None
        self._status = f"Calibration: saved threshold {closed_threshold:.4f}"
        return BlinkCalibrationResult(
            success=True,
            closed_threshold=closed_threshold,
            open_average=open_average,
            closed_average=closed_average,
            reason="saved",
        )

    def _fail(
        self,
        reason: str,
        open_average: float | None = None,
        closed_average: float | None = None,
    ) -> BlinkCalibrationResult:
        self._phase = "idle"
        self._phase_started_ms = None
        self._status = f"Calibration failed: {reason}; keeping previous threshold"
        return BlinkCalibrationResult(
            success=False,
            closed_threshold=None,
            open_average=open_average,
            closed_average=closed_average,
            reason=reason,
        )
