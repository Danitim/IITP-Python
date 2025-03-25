import numpy as np
from tqdm import tqdm


def cubic_kernel(x: float) -> float:
    """Catmull-Rom spline kernel with a = -0.5."""
    a = -0.5
    abs_x = np.abs(x)
    if abs_x <= 1:
        res = (a + 2) * abs_x**3 - (a + 3) * abs_x**2 + 1
        return 1e-10 if np.isclose(res, 0) else res
    if abs_x < 2:
        return a * abs_x**3 - 5 * a * abs_x**2 + 8 * a * abs_x - 4 * a
    return 0.0


def cubic_interpolate(p: np.ndarray, x: float) -> float:
    return p[1] + 0.5 * x * (
        p[2] - p[0] + x * (2.0 * p[0] - 5.0 * p[1] + 4.0 * p[2] - p[3] + x * (3.0 * (p[1] - p[2]) + p[3] - p[0]))
    )


def _fast_bicubic_patch(patch: np.ndarray, dx: float, dy: float) -> float:
    def cubic_interp(p: np.ndarray, x: float) -> float:
        return p[1] + 0.5 * x * (
            p[2] - p[0] + x * (2 * p[0] - 5 * p[1] + 4 * p[2] - p[3] + x * (3 * (p[1] - p[2]) + p[3] - p[0]))
        )

    row_interp = np.array([cubic_interp(patch[i, :], dy) for i in range(4)])
    return float(np.clip(cubic_interp(row_interp, dx), 0, 255))


def spline_interpolation(image: np.ndarray, new_height: int, new_width: int) -> np.ndarray:
    if image.size == 0 or new_height <= 0 or new_width <= 0:
        msg = "Invalid image or output dimensions"
        raise ValueError(msg)

    if image.ndim == 2:
        return _spline_gray(image, new_height, new_width)
    if image.ndim == 3:
        return np.stack(
            [_spline_gray(image[..., c], new_height, new_width, channel=c) for c in range(image.shape[2])],
            axis=-1,
        )
    msg = "Unsupported image dimensions"
    raise ValueError(msg)


def _spline_gray(
    image: np.ndarray,
    new_h: int,
    new_w: int,
    channel: int | None = None,
) -> np.ndarray:
    h, w = image.shape
    _ = h / new_h
    _ = w / new_w

    output = np.zeros((new_h, new_w), dtype=np.uint8)

    bar_desc = f"Spline Interpolation{' (channel ' + str(channel) + ')' if channel is not None else ''}"
    x_coords = np.linspace(0, h - 1, new_h)
    y_coords = np.linspace(0, w - 1, new_w)

    for i, x in enumerate(tqdm(x_coords, desc=bar_desc, unit="line")):
        x_int = int(np.floor(x))
        dx = x - x_int

        x_idx = np.clip(np.arange(x_int - 1, x_int + 3), 0, h - 1)

        for j, y in enumerate(y_coords):
            y_int = int(np.floor(y))
            dy = y - y_int

            y_idx = np.clip(np.arange(y_int - 1, y_int + 3), 0, w - 1)

            patch = image[np.ix_(x_idx, y_idx)].astype(np.float32)
            output[i, j] = int(_fast_bicubic_patch(patch, dx, dy))

    return output
