
# http://www.physics.sfasu.edu/astro/color/spectra.html

def wl_to_rgb(wl):
    r = 0.
    g = 0.
    b = 0.
    if wl >= 380 and wl <= 440:
        r = -1.*(wl-440.)/(440.-380.)
        g = 0.
        b = 1.
    if wl >= 440 and wl <= 490:
        r = 0.
        g = (wl-440.)/(490.-440.)
        b = 1.
    if wl >= 490 and wl <= 510:
        r = 0.
        g = 1.
        b = -1.*(wl-510.)/(510.-490.)
    if wl >= 510 and wl <= 580:
        r = (wl-510.)/(580.-510.)
        g = 1.
        b = 0.
    if ((wl >= 580.) and (wl <= 645.)):
        r = 1.
        g = -1.*(wl-645.)/(645.-580.)
        b = 0.
    if ((wl >= 645.) and (wl <= 780.)):
        r = 1.
        g = 0.
        b = 0.

    # Let the intensity sss fall off near the vision limits
    sss = 1.
    if (wl > 700.):
        sss=.3+.7*(780.-wl)/(780.-700.)
    elif (wl < 420.):
        sss=.3+.7*(wl-380.)/(420.-380.)
    return (sss*r,sss*g,sss*b)

def wl_to_rgb_gamma(wl):
    r, g, b = wl_to_rgb(wl)

    # gamma adjust and write image to an array
    gamma = 0.8
    r = (r)**gamma
    g = (g)**gamma
    b = (b)**gamma
    return (r, g, b)
