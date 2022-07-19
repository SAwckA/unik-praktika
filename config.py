BACKGROUND_IMAGE = 'img/fon.jpg'
BUTTON_TEXT_COLOR = (255, 255, 255)
FONT_NAME = 'Arial'
FONT_SIZE = 40

COLOR_T = tuple[int, int, int]


def to_fixed(num, digits=0):
    """Цифры после запятой"""
    return f"{num:.{digits}f}"


class COLORS:
    WHITE: COLOR_T = (255, 255, 255)
    BLACK: COLOR_T = (0, 0, 0)
    GREEN: COLOR_T = (0, 255, 0)
    RED: COLOR_T = (255, 0, 0)
    BLUE: COLOR_T = (0, 0, 255)


SHOW_DEBUG_BOXES = False

BUTTON_NORMAL_COLOR:COLOR_T = COLORS.BLUE
BUTTON_HOVER_COLOR:COLOR_T = COLORS.GREEN
BUTTON_PRESSED_COLOR:COLOR_T = COLORS.RED
