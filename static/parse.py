import csv

# Define the input and output file paths
import os
input_file_path = os.path.join(os.path.dirname(__file__), 'leetcode_problem_input.txt')
output_file_path = os.path.join(os.path.dirname(__file__), 'leetcode_problem_output.csv')
if not os.path.exists(output_file_path):
    with open(output_file_path, 'w') as file:
        file.write('')

# Read the text file
with open(input_file_path, 'r') as file:
    lines = file.readlines()

# Prepare the CSV file
with open(output_file_path, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    # Write the header
    csvwriter.writerow(['Problem ID', 'Problem Name', 'Difficulty', 'Acceptance Rate'])

    # Iterate over the lines in pairs
    for i in range(0, len(lines)-3, 3):
        # Strip newline characters
        problem_number, problem_name= lines[i].strip().split('. ',1)
        difficulty = lines[i+1].strip()
        percentage = lines[i+2].strip()

        print(difficulty, problem_number, problem_name, percentage)

        # Write the row to the CSV
        csvwriter.writerow([problem_number, problem_name, difficulty, percentage])