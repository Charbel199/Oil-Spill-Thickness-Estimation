import numpy as np


import numpy as np


def _interpolant(t):
    return t*t*t*(t*(t*6 - 15) + 10)


def _generate_perlin_noise_2d(
        shape, res, tileable=(False, False), interpolant=_interpolant
):
    """Generate a 2D numpy array of perlin noise.
    Args:
        shape: The shape of the generated array (tuple of two ints).
            This must be a multple of res.
        res: The number of periods of noise to generate along each
            axis (tuple of two ints). Note shape must be a multiple of
            res.
        tileable: If the noise should be tileable along each axis
            (tuple of two bools). Defaults to (False, False).
        interpolant: The interpolation function, defaults to
            t*t*t*(t*(t*6 - 15) + 10).
    Returns:
        A numpy array of shape shape with the generated noise.
    Raises:
        ValueError: If shape is not a multiple of res.
    """
    delta = (res[0] / shape[0], res[1] / shape[1])
    d = (shape[0] // res[0], shape[1] // res[1])
    grid = np.mgrid[0:res[0]:delta[0], 0:res[1]:delta[1]]\
             .transpose(1, 2, 0) % 1
    # Gradients
    angles = 2*np.pi*np.random.rand(res[0]+1, res[1]+1)
    gradients = np.dstack((np.cos(angles), np.sin(angles)))
    if tileable[0]:
        gradients[-1,:] = gradients[0,:]
    if tileable[1]:
        gradients[:,-1] = gradients[:,0]
    gradients = gradients.repeat(d[0], 0).repeat(d[1], 1)
    g00 = gradients[    :-d[0],    :-d[1]]
    g10 = gradients[d[0]:     ,    :-d[1]]
    g01 = gradients[    :-d[0],d[1]:     ]
    g11 = gradients[d[0]:     ,d[1]:     ]
    # Ramps
    n00 = np.sum(np.dstack((grid[:,:,0]  , grid[:,:,1]  )) * g00, 2)
    n10 = np.sum(np.dstack((grid[:,:,0]-1, grid[:,:,1]  )) * g10, 2)
    n01 = np.sum(np.dstack((grid[:,:,0]  , grid[:,:,1]-1)) * g01, 2)
    n11 = np.sum(np.dstack((grid[:,:,0]-1, grid[:,:,1]-1)) * g11, 2)
    # Interpolation
    t = interpolant(grid)
    n0 = n00*(1-t[:,:,0]) + t[:,:,0]*n10
    n1 = n01*(1-t[:,:,0]) + t[:,:,0]*n11
    return np.sqrt(2)*((1-t[:,:,1])*n0 + t[:,:,1]*n1)


def _generate_fractal_noise_2d(
        shape, res, octaves=1, persistence=0.5,
        lacunarity=2, tileable=(False, False),
        interpolant=_interpolant
):
    """Generate a 2D numpy array of fractal noise.
    Args:
        shape: The shape of the generated array (tuple of two ints).
            This must be a multiple of lacunarity**(octaves-1)*res.
        res: The number of periods of noise to generate along each
            axis (tuple of two ints). Note shape must be a multiple of
            (lacunarity**(octaves-1)*res).
        octaves: The number of octaves in the noise. Defaults to 1.
        persistence: The scaling factor between two octaves.
        lacunarity: The frequency factor between two octaves.
        tileable: If the noise should be tileable along each axis
            (tuple of two bools). Defaults to (False, False).
        interpolant: The, interpolation function, defaults to
            t*t*t*(t*(t*6 - 15) + 10).
    Returns:
        A numpy array of fractal noise and of shape shape generated by
        combining several octaves of perlin noise.
    Raises:
        ValueError: If shape is not a multiple of
            (lacunarity**(octaves-1)*res).
    """
    noise = np.zeros(shape)
    frequency = 1
    amplitude = 1
    for _ in range(octaves):
        noise += amplitude * _generate_perlin_noise_2d(
            shape, (frequency*res[0], frequency*res[1]), tileable, interpolant
        )
        frequency *= lacunarity
        amplitude *= persistence
    return noise


def generate_fractal_environment(smallest_thickness=1, largest_thickness=10, to_int=True, shape=(300, 300), res=(2, 2),
                                 octaves=1, persistence=0.5) -> np.ndarray:
    env = _generate_fractal_noise_2d(shape=shape,
                                     res=res,
                                     octaves=octaves,
                                     persistence=persistence)

    env = np.interp(env, (env.min(), env.max()), (smallest_thickness, largest_thickness))
    env = np.rint(env)
    if to_int:
        env = env.astype('uint8')
    return env


def generate_circle_environment(
        size: int = 500,
        radius_step_size: float = 4 / 100,
        smallest_thickness: int = 0,
        largest_thickness: int = 10,
        step_size: float = 1,
) -> np.ndarray:
    def fill_circle(circle_environment, circle_thickness, circle_radius, circle_center):
        for x in range(len(circle_environment)):
            for y in range(len(circle_environment[0])):
                # 2D Circle formula
                if ((x - circle_center) ** 2 + (y - circle_center) ** 2) < (circle_radius ** 2):
                    circle_environment[x][y] = circle_thickness
        return circle_environment

    if smallest_thickness == 1:
        environment = np.ones(shape=(size, size))
    else:
        environment = np.zeros(shape=(size, size))
    center = int(len(environment) / 2)
    radius = center

    for thickness in np.arange(smallest_thickness, largest_thickness + step_size, step_size):
        environment = fill_circle(environment, thickness, radius, center)
        radius -= int(radius_step_size * size)
    return environment
