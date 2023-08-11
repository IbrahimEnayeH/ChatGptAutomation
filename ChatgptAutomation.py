import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import openai
import pandas as pd
from tkinter import ttk
import time

# Load the API key from the config file
try:
    with open("config.txt", "r") as config_file:
        api_key = config_file.read().strip()
except FileNotFoundError:
    api_key = "your_default_api_key_here"

# Initialize the OpenAI API with the loaded key
openai.api_key = api_key


# Function to count the number of words in a text
def count_words(text):
    words = text.split()
    return len(words)


# Global variables to store the requests and responses
requests_list = []
responses_list = []
processing = False
rate_limit = 3
selected_max_tokens = 100  # Default max tokens value

def update_timer():
    if processing:
        time_elapsed = time.time() - start_time
        requests_done = len(responses_list)
        total_requests = len(requests_list)
        time_per_request = time_elapsed / requests_done if requests_done > 0 else 0
        requests_left = total_requests - requests_done
        estimated_time_left = requests_left * time_per_request
        hours, rem = divmod(estimated_time_left, 3600)
        minutes, seconds = divmod(rem, 60)
        timer_label.config(text=f"Estimated Time Left: {int(hours)}h {int(minutes)}m {int(seconds)}s")
        root.after(1000, update_timer)

def process_phrases():
    # Get the file path from the user
    file_path = filedialog.askopenfilename(filetypes=[('Excel Files', '*.xlsx')])

    if not file_path:  # User cancelled or didn't choose a file
        error_label.config(text="Error: No file selected")
        return

    try:
        # Read data from the Excel file into a pandas DataFrame
        df = pd.read_excel(file_path)

        global requests_list, responses_list, processing, start_time
        requests_list = df['Requests'].tolist()
        responses_list = []

        # Start the timer-like indicator
        processing = True
        start_time = time.time()
        update_timer()

        # Disable the import button during processing
        import_button.config(state="disabled")

        # Get the selected engine from the combobox
        selected_engine = engine_combobox.get()

        # Calculate the time interval between each request based on the rate limit
        time_interval = 60 / rate_limit

        def process_request(index):
            if index >= len(requests_list):
                # Processing completed for all requests
                processing = False
                import_button.config(state="normal")  # Enable the import button

                # Show a message indicating processing is complete
                tk.messagebox.showinfo("Processing Complete", "Phrases processed successfully!")
                error_label.config(text="")  # Clear any previous error messages

                return

            try:
                # Send the phrase to ChatGPT using the selected OpenAI API engine
                response = openai.Completion.create(
                    engine=selected_engine,
                    prompt=requests_list[index],
                    max_tokens=selected_max_tokens  # Use the selected max tokens value
                )

                # Extract the generated response from the API response
                generated_text = response.choices[0].text.strip()

                # Append the response to the list
                responses_list.append(generated_text)

            except Exception as e:
                # If an error occurs, show the error message in the error_label
                error_label.config(text=str(e))
                processing = False  # Stop the timer-like indicator
                import_button.config(state="normal")  # Enable the import button
                return

            # Process the next request after the time interval
            root.after(int(time_interval * 1000), process_request, index + 1)

        # Start processing the first request
        process_request(0)

    except Exception as e:
        # If there is an error reading the Excel file, show the error message in the error_label
        error_label.config(text=str(e))

def save_responses():
    global requests_list, responses_list

    # Check if there are responses to save
    if not requests_list or not responses_list:
        tk.messagebox.showwarning("No Responses", "There are no responses to save.")
        return

    # Prompt the user to choose where to save the responses
    save_file_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel Files', '*.xlsx')])

    if save_file_path:
        # Create a DataFrame with both requests and responses columns
        df = pd.DataFrame({'Requests': requests_list, 'Responses': responses_list})

        # Count the number of words for each row in "Requests" and "Responses" columns
        df['Requests Word Count'] = df['Requests'].apply(count_words)
        df['Responses Word Count'] = df['Responses'].apply(count_words)

        # Save the DataFrame to the selected file
        df.to_excel(save_file_path, index=False)

        # Show a message indicating the responses are saved
        tk.messagebox.showinfo("Responses Saved", "Responses have been successfully saved!")
        error_label.config(text="")  # Clear any previous error messages

def display_credit_window():
    # Create a new top-level window for displaying credit information
    credit_window = tk.Toplevel(root)
    credit_window.title("Credit")

    # Create a Label widget to display the credit information
    credit_label = tk.Label(credit_window, text="Credit to Ibrahim Enayeh", fg="green", font=("Helvetica", 20))
    credit_label.pack(padx=20, pady=20)

def set_rate_limit():
    global rate_limit
    try:
        rate_limit = int(rate_limit_entry.get())
        if rate_limit <= 0:
            raise ValueError("Rate limit must be a positive integer.")
        rate_limit_label.config(text=f"Rate Limit: {rate_limit} requests per minute")
        rate_limit_entry.delete(0, tk.END)
        rate_limit_entry.insert(0, rate_limit)
        rate_limit_error_label.config(text="")
    except ValueError:
        rate_limit_error_label.config(text="Error: Please enter a positive integer.")

def set_max_tokens():
    global selected_max_tokens
    try:
        selected_max_tokens = int(max_tokens_entry.get())
        if selected_max_tokens <= 0:
            raise ValueError("Max tokens must be a positive integer.")
        max_tokens_label.config(text=f"Max Tokens: {selected_max_tokens}")
        max_tokens_entry.delete(0, tk.END)
        max_tokens_entry.insert(0, selected_max_tokens)
        max_tokens_error_label.config(text="")
    except ValueError:
        max_tokens_error_label.config(text="Error: Please enter a positive integer.")

# Function to change the API key
def change_api_key():
    new_api_key = simpledialog.askstring("Change API Key", "Enter the new API key:")
    if new_api_key:
        # Update the API key in memory
        openai.api_key = new_api_key
        # Update the API key in the config file
        with open("config.txt", "w") as config_file:
            config_file.write(new_api_key)
        tk.messagebox.showinfo("API Key Updated", "API key has been updated successfully.")


# Create the main GUI window
root = tk.Tk()
root.title("ChatGPT Responses")
root.geometry("500x700")

# Style configuration for ttk widgets
style = ttk.Style(root)
style.configure('TButton', font=('Helvetica', 12), padding=10)
style.configure('TLabel', font=('Helvetica', 14))

# Create the widgets
import_button = ttk.Button(root, text="Import Excel File", command=process_phrases)
save_button = ttk.Button(root, text="Save Responses", command=save_responses)

# Create a Label widget to show error messages
error_label = tk.Label(root, text="", fg="red")

# Create a Label widget for the timer-like indicator
timer_label = tk.Label(root, text="", fg="blue")

# Create a Menu Bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Create an "Edit" menu
edit_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Edit", menu=edit_menu)

# Add "Change API Key" option in the "Edit" menu
edit_menu.add_command(label="Change API Key", command=change_api_key)

# Create an "About" menu with a "Credit" option
about_menu = tk.Menu(menu_bar, tearoff=0)
about_menu.add_command(label="Credit", command=display_credit_window)
menu_bar.add_cascade(label="About", menu=about_menu)

# Create a Label widget to display the credit information
credit_label = tk.Label(root, text="", fg="green", font=("Helvetica", 20))

# Available OpenAI API engines
engines = ["text-davinci-002", "text-davinci", "text-codex"]


# Create a Combobox widget to select the engine
engine_combobox = ttk.Combobox(root, values=engines, state="readonly")
engine_combobox.set("text-davinci-002")  # Set the default selected engine

# Rate Limiter Widgets
rate_limit_label = tk.Label(root, text=f"Rate Limit: {rate_limit} requests per minute", font=('Helvetica', 12))
rate_limit_entry = tk.Entry(root, font=('Helvetica', 12), width=10)
rate_limit_set_button = ttk.Button(root, text="Set Rate Limit", command=set_rate_limit)
rate_limit_error_label = tk.Label(root, text="", fg="red")

# Pack the widgets vertically with padding
import_button.pack(pady=20)
save_button.pack(pady=20)
error_label.pack(pady=10)
timer_label.pack(pady=10)
credit_label.pack(pady=20)

# Place the engine_combobox in the top-right corner
engine_combobox.place(relx=0.85, rely=0.03, anchor=tk.CENTER)

# Pack rate limiter widgets vertically with padding
rate_limit_label.pack(pady=10)
rate_limit_entry.pack(pady=5)
rate_limit_set_button.pack(pady=5)
rate_limit_error_label.pack(pady=5)

# ... (max tokens widgets)
# Create the widgets for max tokens
max_tokens_label = tk.Label(root, text=f"Max Tokens: {selected_max_tokens}", font=('Helvetica', 12))
max_tokens_entry = tk.Entry(root, font=('Helvetica', 12), width=10)
max_tokens_set_button = ttk.Button(root, text="Set Max Tokens", command=set_max_tokens)
max_tokens_error_label = tk.Label(root, text="", fg="red")

# Pack the widgets vertically with padding
max_tokens_label.pack(pady=10)
max_tokens_entry.pack(pady=5)
max_tokens_set_button.pack(pady=5)
max_tokens_error_label.pack(pady=5)


# Start the main event loop
root.mainloop()