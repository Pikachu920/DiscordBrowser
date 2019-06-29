from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from io import BytesIO
from contextlib import suppress
from PIL import Image


CURSOR_IMAGE = Image.open('./resources/cursor.png')
CURSOR_IMAGE_MASK = CURSOR_IMAGE.convert('RGBA')


def get_driver_dimensions(driver):
    height = driver.execute_script('return window.innerHeight;')
    width = driver.execute_script('return window.innerWidth;')
    return width, height


def get_center_of(driver):
    dimension = get_driver_dimensions(driver)
    return dimension[0] // 2, dimension[1] // 2


def get_screenshot_with_cursor(driver, cursor_position):
    screenshot = Image.open(BytesIO(driver.get_screenshot_as_png()))
    screenshot.paste(CURSOR_IMAGE, tuple(cursor_position), CURSOR_IMAGE_MASK)
    return screenshot


def move_mouse_to(coordinates, driver):
    with suppress(MoveTargetOutOfBoundsException):
        actions = ActionChains(driver)
        body = driver.find_element_by_tag_name('body')
        actions.move_to_element_with_offset(body, -body.location['x'], -body.location['y'])
        actions.move_by_offset(*coordinates)
        actions.perform()


def perform_left_click_at(coordinates, driver):
    move_mouse_to(coordinates, driver)
    ActionChains(driver).click().perform()


def perform_right_click_at(coordinates, driver):
    move_mouse_to(coordinates, driver)
    ActionChains(driver).context_click().perform()


def send_keys(string, driver):
    ActionChains(driver).send_keys(string).perform()