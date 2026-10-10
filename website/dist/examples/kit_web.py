from faceless_champ.web import WebCapture, WebCallout
from facelesschamp_kit.blocks import WebWalkthrough, WebElement

def walkthrough(capture_directory):
    capture = WebCapture(capture_directory)
    return WebWalkthrough(capture, title='Product tour',
                          callouts=(WebCallout('Explore your app', 0, 3),))

def element(capture_directory, selector):
    return WebElement(WebCapture(capture_directory), selector)
