# Hue Terminal exit-code
Do not even ask how i came up with this.

## Usage
Install the requirements:
* Python3
* Request

Edit you `.bashrc`-file and insert:
```bash
PROMPT_COMMAND=__hue_prompt

__hue_prompt() {
        local EXIT=$?
        python3 /home/marcus/repo/hue-exitcode/script.py --exit_code $EXIT

}
```

