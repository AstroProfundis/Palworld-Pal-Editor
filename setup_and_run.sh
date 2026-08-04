if which npm > /dev/null; then
    NPM_CMD=npm
else
    echo "Node is not installed."
fi

cd "./frontend/palworld-pal-editor-webui"
${NPM_CMD} install
${NPM_CMD} run build
cd "../../"
rm -r "./src/palworld_pal_editor/webui"
mv "./frontend/palworld-pal-editor-webui/dist" "./src/palworld_pal_editor/webui"

# Check for Python 3.x and set the appropriate command
if which python3 > /dev/null; then
    PYTHON_CMD=python3
elif which python > /dev/null; then
    PYTHON_CMD=python
else
    echo "Python is not installed."
    exit 1
fi

# Extract the Python version
PYTHON_VERSION=$(${PYTHON_CMD} --version | awk '{print $2}')
PYTHON_MAJOR_VERSION=$(echo ${PYTHON_VERSION} | cut -d. -f1)
PYTHON_MINOR_VERSION=$(echo ${PYTHON_VERSION} | cut -d. -f2)

# Check if Python version is 3.11 or newer
if [ "${PYTHON_MAJOR_VERSION}" -lt 3 ] || { [ "${PYTHON_MAJOR_VERSION}" -eq 3 ] && [ "${PYTHON_MINOR_VERSION}" -lt 11 ]; }; then
    echo "Python version 3.11 or newer is required."
    exit 1
fi

echo "Using ${PYTHON_CMD} (version ${PYTHON_VERSION})"

${PYTHON_CMD} -m venv venv

source venv/bin/activate

pip install -r requirements.txt

# Pin save-tools to the exact commit declared in requirements.txt.
# pip may leave an older build of this git dependency in place, which corrupts
# guild data on save. Detect any drift and force-reinstall just this package.
python - <<'PY'
import json, glob, re, subprocess, sys
url = next((l.strip() for l in open("requirements.txt") if "palworld-save-tools" in l), None)
required = (re.search(r"@([a-f0-9]+)", url).group(1) if url else "").lower()
try:
    info = glob.glob("venv/lib/python*/site-packages/palworld_save_tools*.dist-info/direct_url.json")[0]
    installed = json.load(open(info))["vcs_info"]["commit_id"].lower()
except Exception:
    installed = ""
if installed != required:
    print(f"save-tools {installed[:7] or 'none'} -> {required[:7]}, force reinstalling")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-deps", url])
else:
    print(f"save-tools {installed[:7]} up to date")
PY

pip install -e .

launch_command="python -m palworld_pal_editor ${@}"
echo "Launching $launch_command..."
eval $launch_command