# -*- coding: utf-8 -*-
"""
    lodgeit.captcha
    ~~~~~~~~~~~~~~~

    A module that produces image and audio captchas.  Uses some code of
    PyCAPTCHA by Micah Dowty and was originally used in inyoka.


    :copyright: Copyright 2007-2008 by Armin Ronacher, Micah Dowty.
    :license: BSD
"""
import random
import colorsys
import math
from os import listdir
from os.path import abspath, join, dirname, pardir
from PIL import ImageFont, ImageDraw, Image, ImageChops, ImageColor
from werkzeug import Response
from lodgeit import local

try:
    from hashlib import sha1
except ImportError:
    from sha import new as sha1

resource_path = abspath(join(dirname(__file__), pardir, 'res'))


def check_hashed_solution(solution, hashed_solution=None, secret_key=None):
    """Check a solution against the hashed solution from the first
    request by using the secret key.
    """
    if hashed_solution is None:
        hashed_solution = local.request.session.get('captcha_id')
        if hashed_solution is None:
            return False
    return hashed_solution == calculate_hash(solution, secret_key)


def calculate_hash(solution, secret_key=None):
    """Calculate the hash."""
    if secret_key is None:
        secret_key = local.application.secret_key
    return sha1('%s|%s' % (
        secret_key,
        solution.encode('utf-8')
    )).hexdigest()


def generate_word():
    """This function returns a pronounceable word."""
    consonants = 'bcdfghjklmnprstvwz'
    vowels = 'aeiou'
    both = consonants + vowels
    length = random.randrange(8, 12)
    return ''.join(
        random.choice(consonants) +
        random.choice(vowels) +
        random.choice(both) for x in xrange(length // 3)
    )[:length]


def get_random_resource(type, prefix=None):
    """Return a random resource of a given type."""
    path = join(resource_path, type)
    choices = (x for x in listdir(path) if not x.startswith('.'))
    if prefix is not None:
        choices = (x for x in choices if x.startswith(prefix))
    return join(path, random.choice(tuple(choices)))


def random_color(saturation=0.5, lumination=None):
    """Return a random number with the given saturation."""
    hue = random.random()
    if lumination is None:
        lumination = random.random()
    r, g, b = colorsys.hls_to_rgb(hue, lumination, saturation)
    return '#%02x%02x%02x' % (
        int(r * 255) & 0xff,
        int(g * 255) & 0xff,
        int(b * 255) & 0xff
    )


class Captcha(object):
    """Represents a captcha."""
    default_size = (300, 100)

    def __init__(self, solution=None):
        if solution is None:
            solution = generate_word()
        self.solution = solution
        self.layers = [
            RandomBackground(),
            RandomDistortion()
        ]
        text_layer = TextLayer(self.solution, bg=self.layers[0].bg)
        self.layers.extend((text_layer, SineWarp()))

    def hash_solution(self, secret_key=None):
        """Return the solution as hashed value."""
        return calculate_hash(self.solution, secret_key)

    def render_image(self, size=None):
        if size is None:
            size = self.default_size
        image = Image.new('RGBA', size)
        for layer in self.layers:
            image = layer.render(image)
        return image

    def get_response(self, size=None, set_cookie=False):
        response = Response(mimetype='image/png')
        self.render_image(size=None).save(response.stream, 'PNG')
        if set_cookie:
            local.request.session['captcha_id'] = self.hash_solution()
        return response


class Layer(object):
    """Baseclass for a captcha layer."""
    bg = 'dark'

    def render(self, image):
        return image


class TextLayer(Layer):
    """Add text to the captcha."""
    bg = 'transparent'

    def __init__(self, text, min_size=32, max_size=48, bg='dark'):
        self.text = text
        self.alignment = (random.random(), random.random())
        if bg == 'dark':
            color = random_color(saturation=0.3, lumination=0.8)
        else:
            color = random_color(saturation=0.1, lumination=0.1)
        self.text_color = color
        self.transparency = random.randint(20, 60)
        self.font = ImageFont.truetype(get_random_resource('fonts'),
                                       random.randrange(min_size, max_size))

    def render(self, image):
        text_layer = Image.new('RGB', image.size, (0, 0, 0))
        alpha = Image.new('L', image.size, 0)

        # draw grayscale image white on black
        text_image = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(text_image)
        text_size = self.font.getsize(self.text)
        x = int((image.size[0] - text_size[0]) * self.alignment[0] + 0.5)
        y = int((image.size[1] - text_size[1]) * self.alignment[1] + 0.5)
        draw.text((x, y), self.text, font=self.font,
                  fill=255 - self.transparency)

        # colorize the text and calculate the alpha channel
        alpha = ImageChops.lighter(alpha, text_image)
        color_layer = Image.new('RGBA', image.size, self.text_color)
        mask = Image.eval(text_image, lambda x: 255 * (x != 0))
        text_layer = Image.composite(color_layer, text_layer, mask)

        # paste the text on the image with the correct alphachannel
        image.paste(text_layer, alpha)
        return image


class CombinedLayer(Layer):
    """Combines multiple layers."""

    def __init__(self, layers):
        self.layers = layers
        if layers:
            self.bg = layers[0].bg

    def render(self, image):
        for layer in self.layers:
            image = layer.render(image)
        return image


class RandomBackground(CombinedLayer):
    """Selects a random background."""

    def __init__(self):
        layers = [random.choice([SolidColor, DarkBackground,
                                 LightBackground])()]
        for x in xrange(random.randrange(1, 4)):
            layers.append(random.choice([
                NoiseBackground,
                GridBackground
            ])())
        CombinedLayer.__init__(self, layers)
        self.bg = layers[0].bg


class RandomDistortion(CombinedLayer):
    """Selects a random distortion."""
    background = 'transparent'

    def __init__(self):
        layers = []
        for x in xrange(random.randrange(1, 3)):
            layers.append(random.choice((
                WigglyBlocks,
                SineWarp
            ))())
        CombinedLayer.__init__(self, layers)


class Picture(Layer):
    """Add a background to the captcha."""

    def __init__(self, picture):
        self.image = Image.open(picture)
        self.offset = (random.random(), random.random())

    def render(self, image):
        tile = self.image
        for j in xrange(-1, int(image.size[1] / tile.size[1]) + 1):
            for i in xrange(-1, int(image.size[0] / tile.size[0]) + 1):
                dest = (int((self.offset[0] + i) * tile.size[0]),
                        int((self.offset[1] + j) * tile.size[1]))
                image.paste(tile, dest)
        return image


class LightBackground(Picture):
    bg = 'light'

    def __init__(self):
        Picture.__init__(self, get_random_resource('backgrounds/light'))


class DarkBackground(Picture):

    def __init__(self):
        Picture.__init__(self, get_random_resource('backgrounds/dark'))


class NoiseBackground(Layer):
    """Add some noise as background.  You can combine this with another
    background layer.
    """
    bg = 'transparent'

    def __init__(self, saturation=0.1, num_dots=None):
        self.saturation = saturation
        self.num_dots = random.randrange(300, 500)
        self.seed = random.random()

    def render(self, image):
        r = random.Random(self.seed)
        for i in xrange(self.num_dots):
            dot_size = random.randrange(1, 5)
            bx = int(r.uniform(0, image.size[0] - dot_size))
            by = int(r.uniform(0, image.size[1] - dot_size))
            image.paste(random_color(self.saturation, 0.4),
                        (bx, by, bx + dot_size - 1,
                         by + dot_size - 1))
        return image


class GridBackground(Layer):
    """Add a grid as background.  You can combine this with another
    background layer.
    """
    bg = 'transparent'

    def __init__(self, size=None, color=None):
        if size is None:
            size = random.randrange(10, 50)
        if color is None:
            color = random_color(0, 0.4)
        self.size = size
        self.color = color
        self.offset = (random.uniform(0, self.size),
                       random.uniform(0, self.size))

    def render(self, image):
        draw = ImageDraw.Draw(image)
        for i in xrange(image.size[0] / self.size + 1):
            draw.line((i * self.size + self.offset[0], 0,
                       i * self.size + self.offset[0], image.size[1]),
                      fill=self.color)
        for i in xrange(image.size[0] / self.size + 1):
            draw.line((0, i * self.size + self.offset[1],
                       image.size[0], i * self.size+self.offset[1]),
                       fill=self.color)
        return image


class SolidColor(Layer):
    """A solid color background.  Very weak on its own, but good
    to combine with other backgrounds.
    """

    def __init__(self, color=None):
        if color is None:
            color = random_color(0.2, random.random() > 0.5 and 0.3 or 0.7)
        self.color = ImageColor.getrgb(color)
        if colorsys.rgb_to_hls(*[x / 255.0 for x in self.color])[1] > 0.5:
            self.bg = 'light'

    def render(self, image):
        image.paste(self.color)
        return image


class WigglyBlocks(Layer):
    """Randomly select and shift blocks of the image"""
    bg = 'transparent'

    def __init__(self, block_size=None, sigma=0.01, iterations=None):
        if block_size is None:
            block_size = random.randrange(15, 25)
        if iterations is None:
            iterations = random.randrange(250, 350)
        self.block_size = block_size
        self.sigma = sigma
        self.iterations = iterations
        self.seed = random.random()

    def render(self, image):
        r = random.Random(self.seed)
        for i in xrange(self.iterations):
            # Select a block
            bx = int(r.uniform(0, image.size[0] - self.block_size))
            by = int(r.uniform(0, image.size[1] - self.block_size))
            block = image.crop((bx, by, bx + self.block_size - 1,
                                by + self.block_size - 1))

            # Figure out how much to move it.
            # The call to floor() is important so we always round toward
            # 0 rather than to -inf. Just int() would bias the block motion.
            mx = int(math.floor(r.normalvariate(0, self.sigma)))
            my = int(math.floor(r.normalvariate(0, self.sigma)))

            # Now actually move the block
            image.paste(block, (bx+mx, by+my))
        return image


class WarpBase(Layer):
    """Abstract base class for image warping.  Subclasses define a function
    that maps points in the output image to points in the input image.  This
    warping engine runs a grid of points through this transform and uses PIL's
    mesh transform to warp the image.
    """
    bg = 'transparent'
    filtering = Image.BILINEAR
    resolution = 10

    def get_transform(self, image):
        """Return a transformation function, subclasses should override this"""
        return lambda x, y: (x, y)

    def render(self, image):
        r = self.resolution
        x_points = image.size[0] / r + 2
        y_points = image.size[1] / r + 2
        f = self.get_transform(image)

        # Create a list of arrays with transformed points
        x_rows = []
        y_rows = []
        for j in xrange(y_points):
            x_row = []
            y_row = []
            for i in xrange(x_points):
                x, y = f(i * r, j * r)

                # Clamp the edges so we don't get black undefined areas
                x = max(0, min(image.size[0] - 1, x))
                y = max(0, min(image.size[1] - 1, y))

                x_row.append(x)
                y_row.append(y)
            x_rows.append(x_row)
            y_rows.append(y_row)

        # Create the mesh list, with a transformation for
        # each square between points on the grid
        mesh = []
        for j in xrange(y_points - 1):
            for i in xrange(x_points-1):
                mesh.append((
                    # Destination rectangle
                    (i * r, j * r, (i + 1) * r, (j + 1) * r),
                    # Source quadrilateral
                    (x_rows[j][i], y_rows[j][i],
                     x_rows[j + 1][i], y_rows[j+1][i],
                     x_rows[j + 1][i + 1], y_rows[j + 1][i + 1],
                     x_rows[j][i+1], y_rows[j][i + 1]),
                ))
        return image.transform(image.size, Image.MESH, mesh, self.filtering)


class SineWarp(WarpBase):
    """Warp the image using a random composition of sine waves"""

    def __init__(self, amplitude_range=(3, 6.5), period_range=(0.04, 0.1)):
        self.amplitude = random.uniform(*amplitude_range)
        self.period = random.uniform(*period_range)
        self.offset = (random.uniform(0, math.pi * 2 / self.period),
                       random.uniform(0, math.pi * 2 / self.period))

    def get_transform(self, image):
        return (lambda x, y, a=self.amplitude, p=self.period,
                       o=self.offset: (math.sin((y + o[0]) * p) * a + x,
                                       math.sin((x + o[1]) * p) * a + y))
