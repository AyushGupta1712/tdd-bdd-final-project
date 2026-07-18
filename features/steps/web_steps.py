from behave import when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions

# =================================================================
# NAVIGATION & GENERAL STEPS
# =================================================================

@when('I visit the "Home Page"')
def step_impl(context):
    context.driver.get(context.base_url)

@then('I should see "{text}" in the title')
def step_impl(context, text):
    assert text in context.driver.title

@then('I should not see "{text}"')
def step_impl(context, text):
    assert text not in context.driver.find_element(By.TAG_NAME, 'body').text

# =================================================================
# INTERACTIVE CONTROL STEPS (BUTTONS & DROPDOWNS)
# =================================================================

@when('I press the "{button}" button')
def step_impl(context, button):
    button_id = button.lower() + '-btn'
    
    # Force clear old results text on search to ensure clean asynchronously updated DOM polling
    if button.lower() == 'search':
        try:
            context.driver.execute_script(
                "document.getElementById('search_results').innerText = '';"
            )
        except Exception:
            pass

    context.driver.find_element(By.ID, button_id).click()

@when('I select "{value}" in the "{dropdown_name}" dropdown')
def step_impl(context, value, dropdown_name):
    name_lower = dropdown_name.lower()
    element = None
    
    # Check for search form elements first using find_elements to avoid implicit wait penalties
    for prefix in ['search_', 'product_']:
        elements = context.driver.find_elements(By.ID, prefix + name_lower)
        if elements and elements[0].is_displayed():
            element = elements[0]
            break
            
    if not element:
        element = context.driver.find_element(By.ID, 'product_' + name_lower)

    select = Select(element)
    normalized_value = str(value).strip().lower()

    # Dynamic option match strategy
    target_text = None
    for option in select.options:
        opt_text = option.text.strip().lower()
        opt_val = option.get_attribute('value').strip().lower()
        if normalized_value == opt_text or normalized_value == opt_val:
            target_text = option.text
            break

    if target_text is not None:
        select.select_by_visible_text(target_text)
    else:
        select.select_by_value(value)

    context.driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", element)

# =================================================================
# TEXT DATA MUTATION & SETUP STEPS
# =================================================================

@when('I set the "{field_name}" to "{value}"')
@when('I change the "{field_name}" to "{value}"')
def step_impl(context, field_name, value):
    element_id = 'product_' + field_name.lower()
    element = context.driver.find_element(By.ID, element_id)
    element.clear()
    element.send_keys(value)

# =================================================================
# CLIPBOARD DATA STORAGE (COPY & PASTE OPERATIONS)
# =================================================================

@when('I copy the "{field_name}" field')
def step_impl(context, field_name):
    element_id = 'product_' + field_name.lower()
    context.clipboard = context.driver.find_element(By.ID, element_id).get_attribute('value')

@when('I paste the "{field_name}" field')
def step_impl(context, field_name):
    element_id = 'product_' + field_name.lower()
    element = context.driver.find_element(By.ID, element_id)
    element.clear()
    element.send_keys(context.clipboard)

# =================================================================
# VALIDATION & VERIFICATION STEPS (THEN BLOCKS)
# =================================================================

@then('the "{field_name}" field should be empty')
def step_impl(context, field_name):
    element_id = 'product_' + field_name.lower()
    field_value = context.driver.find_element(By.ID, element_id).get_attribute('value')
    assert field_value == ""

@then('I should see "{expected_value}" in the "{field_name}" field')
def step_impl(context, expected_value, field_name):
    element_id = 'product_' + field_name.lower()
    actual_value = context.driver.find_element(By.ID, element_id).get_attribute('value')
    assert actual_value == expected_value

@then('I should see "{expected_value}" in the "{dropdown_name}" dropdown')
def step_impl(context, expected_value, dropdown_name):
    element_id = 'product_' + dropdown_name.lower()
    select = Select(context.driver.find_element(By.ID, element_id))
    assert select.first_selected_option.text.upper() == expected_value.upper()

@then('I should see "{name}" in the results')
def step_impl(context, name):
    found = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, 'search_results'),
            name
        )
    )
    assert found

@then('I should not see "{name}" in the results')
def step_impl(context, name):
    # Ensure any background active processing completes before validating absence
    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.invisibility_of_element_located((By.ID, 'flash_message_loading'))
    )
    results_text = context.driver.find_element(By.ID, 'search_results').text
    assert name not in results_text

@then('I should see the message "{message}"')
def step_impl(context, message):
    found = WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, 'flash_message'),
            message
        )
    )
    assert found