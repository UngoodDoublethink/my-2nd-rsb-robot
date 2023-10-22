from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    # browser.configure(
    #     slowmo=100,
    # )
    open_robot_order_website()
    orders = get_orders()
    for order in orders:
        close_annoying_modal()
        fill_the_form(order)
        submit_order()
        pdf_file = store_receipt_as_pdf(order["Order number"])
        bot_file = take_robot_screenshot(order["Order number"])
        embed_screenshot_to_receipt(bot_file, pdf_file)
        create_next_order()
        archive_receipts()
    print( "Done ordering" )



def create_next_order():
    page = browser.page()
    page.click("#order-another")


def open_robot_order_website():
    """ open a browser and navigate to company intranet"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")


def get_orders():
    """ Download file and Get the orders from file """
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)

    library = Tables()
    orders = library.read_table_from_csv(
        "orders.csv"
    )

    return orders


def close_annoying_modal():
    """ Close nasty pop-up """
    page = browser.page()
    page.click(".btn-dark")


def fill_the_form(order):
    """ Wave rights and fill the form with the order data """
    page = browser.page()
    
    # Select the head
    page.select_option("#head",order["Head"])
    # Select the body
    bodyNum = order["Body"]
    page.click(f'input[type="radio"][value="{bodyNum}"]')
    # Select the legs
    legsFieldLocator = "//*[@placeholder='Enter the part number for the legs']"
    legsNum = order["Legs"]
    page.fill( legsFieldLocator, legsNum)
    # Enter the address
    page.fill("#address", order["Address"])


def submit_order():
    """ Submit form and handle errors"""
    page = browser.page()
    page.click("#order")

    # Check for errors    
    errorMessage = page.query_selector(".alert-danger")
    # If error is found, retry. Until it's no longer there.
    while errorMessage:
        print("Error is present")
        # Submit the order 
        page.click("#order")
        # Check if error is still there
        errorMessage = page.query_selector(".alert-danger")


def store_receipt_as_pdf(order_number):
    """ save each order in its own pdf file """
    page = browser.page()
    order_html = page.locator("#receipt").inner_html()

    pdf = PDF()
    pdfFile = f"output/receipts/order_{order_number}_receipt.pdf"
    pdf.html_to_pdf(order_html, pdfFile)
    return pdfFile

def take_robot_screenshot(order_number):
    """ save a screenshot of the order receipt """
    imageFile = f"output/receipts/order_{order_number}_robot_preview.png"

    page = browser.page()
    element = page.query_selector("#robot-preview-image")
    shot  = browser.screenshot(element)
        
    with open(imageFile, "wb") as file:
        file.write(shot)
    return imageFile


# def take_receipt_screenshot(order_number):
#     """ save a screenshot of the order receipt """
#     page = browser.page()
#     #robot-preview-image
#     imageFile = f"output/receipts/order_{order_number}_receipt.png"
#     page.screenshot(path = imageFile)
#     return imageFile


def embed_screenshot_to_receipt(screenshot, pdf_file):
    """ Embed the screenshot into existing PDF"""
    pdf = PDF()

    list_of_files = [
        screenshot
    ]
    
    pdf.add_watermark_image_to_pdf(
        image_path=list_of_files[0],
        source_path=pdf_file,
        output_path=pdf_file
    )



def archive_receipts():
    """ Archive all receipts """
    lib = Archive()
    lib.archive_folder_with_zip('output/receipts/', 'output/receipts.zip', include='*.pdf')
