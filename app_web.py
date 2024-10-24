import streamlit as st
import subprocess
import tempfile
import os
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

def create_api_key_input(key_name, env_var_name):
    """创建API key输入框并处理其逻辑"""
    env_value = os.getenv(env_var_name)
    
    # 创建密码输入框
    api_key = st.text_input(
        f"{key_name} API Key", 
        value=env_value if env_value else "",
        type="password",
        help=f"Enter your {key_name} API key"
    )
    
    # 如果用户输入了新的API key且与环境变量不同
    if api_key and api_key != env_value:
        # 更新.env文件
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # 查找并更新或添加API key
            key_found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{env_var_name} ="):
                    lines[i] = f"{env_var_name} = {api_key}\n"
                    key_found = True
                    break
            
            if not key_found:
                lines.append(f"{env_var_name} = {api_key}\n")
            
            with open(env_path, 'w') as f:
                f.writelines(lines)
            
            # 更新环境变量
            os.environ[env_var_name] = api_key
    
    return api_key

def load_workflows():
    workflows = []
    config_dir = os.path.join(current_dir, 'config')
    for file in os.listdir(config_dir):
        if file.endswith('.yaml'):
            workflows.append(file.replace('.yaml', ''))
    return workflows

def load_config(workflow):
    config_path = os.path.join(current_dir, 'config', f'{workflow}.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Streamlit app
st.title('Text Processing Workflow')

# API Keys section in sidebar
with st.sidebar:
    st.header('API Keys')
    openrouter_api_key = create_api_key_input("OpenRouter", "OPENROUTER_API_KEY")
    exa_api_key = create_api_key_input("EXA", "EXA_API_KEY")

# Workflow selection
workflows = load_workflows()
selected_workflow = st.selectbox('Select Workflow', workflows)

# Load config for selected workflow
config = load_config(selected_workflow)

# Text input
input_text = st.text_area('Enter text to process')

# Process button
if st.button('Process'):
    if input_text:
        # Save input text to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
            temp_file.write(input_text)
            temp_file_path = temp_file.name

        # Prepare command with full path to app.py
        app_path = os.path.join(current_dir, 'app.py')
        cmd = ['poetry', '--directory', current_dir, 'run', 'python', app_path, temp_file_path, '--workflow', selected_workflow]

        # Run the command
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Display output and provide download link
            output_file = os.path.join(os.path.dirname(temp_file_path), f'{selected_workflow}-output.md')
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    output_content = f.read()
                st.text_area('Output', output_content, height=300)
                st.download_button('Download Output', output_content, file_name=f'{selected_workflow}-output.md')
            else:
                st.warning('Output file not found. Displaying standard output and error for debugging:')
                st.text_area('Standard Output', result.stdout, height=300)
                if result.stderr:
                    st.text_area('Standard Error', result.stderr, height=300)

        except subprocess.CalledProcessError as e:
            st.error(f'Error occurred. Displaying standard output and error for debugging:')
            st.text_area('Standard Output', e.stdout, height=300)
            st.text_area('Standard Error', e.stderr, height=300)

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    else:
        st.warning('Please enter some text to process.')
