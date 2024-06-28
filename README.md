# DataDude

Get up to speed quickly.

## Rough Demo


## Getting Started

### Prerequisites

- OpenAI developer account

### Installation

1. Clone repository
2. Install required Python modules
   1. `pip install -r requirements.txt`
3. Add OpenAI token to environment as OPENAI_API_KEY

### Usage

1. Run the datadude server:
   `python server.py`
2. Open a terminal in your desired project's folder
3. Add a .dudeignore file in the desired project folder to exclude any file or folder you don't want referenced by datadude to respond to queries.
   1. Don't include '/' after folder names. Just list the name.
4. Run the datadude client:
   `python client.py`


There are scripts in the tests/ folder to help manage the OpenAI resources used. They show how to use the utility scripts in the ai_utils/ and directory_utils/ folders in the datadude directory.

### Helpful Tips

Here are some tips to save you money and time:

- Run the directory scanner to get a JSON string of your folder's context. Pass that context into the token counter to see how many input tokens the context is. If it's too large, look through the folder and add some files/folders that don't matter to the .dudeignore file.
- Add the install path as an environment variable so you can run the DataDude client anywhere and it knows where to look for some necessary utilities.


### Contributing

DataDude is a work in progress. See docs/Architecture.md for a brief technical summary of the end goal (which is subject to change). Emailing me is the best way to reach me to talk.

## Why?

I recently took on a consulting project where a small business needed help getting their robotic system back online. They had no knowledge of the technical aspects of the system and was on their own after the company that created/installed the system got acquired by and was under an NDA. 

The robots were up in the ceiling, so I decided to do everything I could to diagnose any issues outside of the robot before looking at them. After determining that everything on the app side looked good, I decided to try to look at the code on the onboard computer.

Fortunately, it had a Linux OS. However, I still knew very little about the system worked, so I needed to figure that out as quickly as possible - and I was very time constrained because the business was still active. I had gone there after hours overnight. It was not a comfy situation - no desks available to work. Because I had to get the robots from the ceiling and remove the onboard computer to see the code, I couldn't do live tests. I didn't have administrative access to ssh into the system.

Due to time constraints and physical constraints *(super hungry and thirsty)* I decided to copy the source code folder to a flash drive so I could inspect it at home, so I could put the robots back into the ceiling and clean up before the business opened in the morning. It became clear that I needed to inspect things more closely and spend a lot more time on it. Along with the source code, I needed to understand how it interacted with two user applications wirelessly, as well as how it interfaced/interacted with the hardware.
*(Upon reflection, I should've just taken one of the robots home with me. Could've worked way faster.)*

Ultimately, I left the project because it wasn't important enough to the business to justify me spending so much time on it, unless it was for free *(which I would've loved to do to crack the problem, but decided against due to the first reason)*. Their customers had gotten used to it not working and the core business was okay. It was just a nice-to-have. And that was a great lesson for me.

As I left the project, I asked myself if there was something I could've done better. An obvious one was looking at the robot sooner, and troubleshooting all the hardware components first before even looking at the onboard computer. But outside of that, I asked why it took so much time looking at the system, and if I could've understood everything a lot faster. That thought birthed this tool.
*(Yes, one skeptical thought you are right to have is "maybe you're just a noob". That's fair. Before starting this project, I did pick up a copy of the Art of Unix Programming to read over. But that's besides the point!)*
