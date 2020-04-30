import matplotlib.pyplot as plt
import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver import ActionChains
import time
import io
from PIL import Image
import base64

# Facebook login
facebook_username = "xxxxxx@gmail.com"
facebook_password = "xxxxxx"


# Canvas size
H, W = 1280, 720

# Some hard-coded values:
# Actual Canvas Size
h, w = 763, 407
# Start Button Location
start_button_x = 350
start_button_y = 1100

errors = 0

def login_to_facebook(username, password, driver):
	driver.get("https://www.facebook.com")
	username_box = driver.find_element_by_id("email")
	password_box = driver.find_element_by_id("pass")
	submit   = driver.find_element_by_id("loginbutton")
	username_box.send_keys(username)
	password_box.send_keys(password)
	submit.click()

def get_screenshot(driver, canvas):
	canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
	canvas_png = base64.b64decode(canvas_base64)
	imageStream = io.BytesIO(canvas_png)
	imageFile = Image.open(imageStream)
	img = np.array(imageFile)
	return img

def click_on(x, y, driver):
	xa, ya = get_adjusted_coords(x, y)
	action = ActionChains(driver)
	action.reset_actions()
	action.move_by_offset(xa, ya)
	action.click()
	action.perform()

def get_adjusted_coords(x, y):
	return x / W * w, y / H * h

def get_diff_circle(img, offset=450, box=5):
	global errors
	try:
		gray = (cv2.cvtColor(img[offset:, :], cv2.COLOR_RGBA2GRAY)* 255).astype(np.uint8)
		circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 3.5, 80, maxRadius=100)[0] # Find alls circles

		assert len(circles) in [4, 9, 16, 25, 36, 49, 64, 81], ("Error: Found {} circles".format(len(circles)))

		# Find color of each circle
		colors = []
		for circle in circles:
			x, y, r = (circle)
			# Determine color based on a small area around the center
			colors.append(np.mean(img[int(y)+offset-box:int(y)+offset+box, int(x)-box:int(x)+box]))

		assert len(set(colors)) == 2, "Found {} distinct colors".format(len(set(colors)))
		
		# Find circle with unique color
		for i, c in enumerate(colors):
			if colors.count(c) == 1:
				x, y, r = (circles[i])
				return x, y+offset, r

	except AssertionError as e:
		# plt.imsave('img{}.png'.format(errors), img)
		errors += 1
		print (e)
		return

end = plt.imread('end.png')
def check_end_game(img):
	time_remainging = img[200:300, 500:650]
	return (np.array_equal(end, time_remainging))



if __name__ == "__main__":

	# Initialize driver
	driver = webdriver.Firefox()

	login_to_facebook(facebook_username, facebook_password, driver)

	# Navigate to Lyto Game
	driver.get("https://www.facebook.com/instantgames/1099543880229447")
	time.sleep(10)

	# Switch focus to game canvas
	driver.switch_to_frame(driver.find_element_by_tag_name("iframe"))
	canvas = driver.find_element_by_tag_name('canvas')

	# Click Start Button
	click_on(start_button_x, start_button_y, driver)
	time.sleep(3)

	level = 0
	cur_level_count = 1
	prev_level = 0

	while True:
		print ("Level: ", level)
		img = get_screenshot(driver, canvas)

		# Stop if stucked
		if prev_level == level:
			cur_level_count += 1
			if cur_level_count > 20:
				print ("Stopped")
				break
		else:
			prev_level = level
			cur_level_count = 1

		
		try:
			x, y, r = get_diff_circle(img)
			click_on(x, y, driver)
			time.sleep(0.1)
			level += 1
			
		except TypeError as e:
			if check_end_game(img):
				break
			time.sleep(0.01)
	

	# Do what you want, i.e. share your results
	time.sleep(120)

