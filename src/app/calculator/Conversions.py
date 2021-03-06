import numpy as np 

from ..utility import Vector2D


# from ..Models import Model
def angleToPixel(angles, model):
    """
    Provides simple conversions between angle measurements to pixel coordinates. angles can be a numpy array, or a Vector2D instance.
    If no parameters are supplied, uses default parameters
    """
    parameters = model.parameters
    canvasDim = parameters.canvasDim
    dTheta = parameters.dTheta.to('rad').value
    ret = angles.copy()
    if isinstance(angles, np.ndarray):
        ret[:, 0] = (angles[:, 0] / dTheta) + canvasDim / 2
        ret[:, 1] = canvasDim / 2 - (angles[:, 1] / dTheta)
        return ret
    else:
        angles2 = angles.to('rad') / dTheta
        return Vector2D(angles2.x + canvasDim / 2, canvasDim / 2 - angles2.y)


def pixelToAngle(pixels, model):
    """
    Provides simple conversions between pixel coordinates and angle measurements. pixels can be a numpy array, or a Vector2D instance.
    If no parameters are supplied, uses default parameters
    """
    parameters = model.parameters
    canvasDim = parameters.canvasDim
    dTheta = parameters.dTheta.to('rad').value

    if isinstance(pixels, np.ndarray):
        pixels[:, 0] = (pixels + canvasDim / 2) * dTheta
        pixels[:, 1] = (canvasDim / 2 - pixels) * dTheta
        return pixels
    else:
        pixels = pixels * dTheta
        return Vector2D(pixels.x + canvasDim / 2, canvasDim / 2 - pixels.y, 'rad')
