import streamlit as st
import glob
import zipfile
import tempfile
from pathlib import Path
from langchain_together import ChatTogether
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai.llms import GoogleGenerativeAI
from langchain.chains import LLMChain

def list_code_files(directory):
    """List all files with coding extensions in the provided directory."""
    code_extensions = ['*.py', '*.js', '*.java', '*.cpp', '*.c', '*.rb', '*.ipynb','*.html','*.css','*.js']
    files = []
    for ext in code_extensions:
        files.extend(glob.glob(str(directory / '**' / ext), recursive=True))
    return files


def debug_code_with_llama(file_path):
    """Use LLaMA AI to debug and modify the code file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        human = HumanMessagePromptTemplate.from_template(
            """{file_content}"""
        )

        system = SystemMessagePromptTemplate.from_template(
            """Act as a code debugger. Do not provide explanations, only the corrected code. Identify and resolve issues such as syntax errors, inefficiencies, logic flaws, incomplete code, missing imports, and incomplete packages, modules, or files. Ensure the code is optimized and fully functional with the necessary fixes. """
        )

        llm = ChatTogether(
            model="meta-llama/Llama-Vision-Free",
            api_key=st.secrets['together'],
        )
        
        model = GoogleGenerativeAI(
            api_key=st.secrets['google'],
            model='gemini-1.5-flash', 
            verbose=True
        )

 

        chat_template = ChatPromptTemplate.from_messages([system, human])
        str_output = StrOutputParser()


        conversation = LLMChain(
        llm=model,
        prompt=chat_template,
        verbose=True,
        )
        chain = chat_template | model | str_output
        input_data = {'file_content': file_content}
        # response = conversation.invoke(input_data)['text']
        response = chain.invoke(input_data)
        return response
    except Exception as e:
        st.error(f"Error during debugging with LLaMA: {str(e)}")
        return None


def create_zip_from_files(files, zip_name):
    """Create a ZIP archive from the list of files."""
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for file in files:
            zipf.write(file, Path(file).name)


# Streamlit app title
st.title('🛠️ AI-Powered Code Debugger with LLaMA')
st.write("List all files with coding extensions in the provided directory. ['*.py', '*.js', '*.java', '*.cpp', '*.c', '*.rb', '*.ipynb','*.html','*.css','*.js']")
# File uploader for ZIP file
uploaded_file = st.file_uploader("📁 Upload a ZIP file containing your entire folder", type=['zip'])

if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as temp_dir:  # Create temp directory
        extract_path = Path(temp_dir)  # Create path object for temp directory
        
        try:
            st.write(f"📂 Extracting files to temporary folder: `{extract_path}`")
            
            # Extract ZIP into temporary directory
            with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                zip_ref.extractall(extract_path) 
                st.success(f"✅ Files extracted successfully to: `{extract_path}`")
            
            # List the extracted files
            extracted_files = list(extract_path.glob('**/*'))  # List all files and folders
            if extracted_files:
                st.write("📜 **Extracted Files:**")
                for file in extracted_files:
                    st.write(f"📄 {file}")
            else:
                st.warning("⚠️ No files were found in the extracted folder.")
            
            if st.button('🔍 Process Files'):
                st.write("📂 **Processing files...**")
                
                # Create a temporary directory for processed files
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_dir_path = Path(temp_dir)
                    
                    # List all files in the extracted folder
                    code_files = list_code_files(extract_path)
                    
                    if code_files:
                        modified_files = []
                        
                        for file in code_files:
                            try:
                                st.write(f"⚙️ Debugging `{file}`...")
                                debug_response = debug_code_with_llama(file)
                                
                                if debug_response:
                                    file_name = Path(file).stem  # Get the filename without extension
                                    file_ext = Path(file).suffix  # Get the file extension
                                    
                                    new_file_path = temp_dir_path / f"{file_name}_debugged{file_ext}"
                                    
                                    with open(new_file_path, 'w', encoding='utf-8') as f:
                                        f.write(debug_response)
                                    
                                    modified_files.append(new_file_path)
                                    st.success(f"✅ File `{file}` successfully debugged and saved as `{new_file_path}`.")
                                
                            except Exception as e:
                                st.error(f"❌ Error processing file `{file}`: {str(e)}")

                        if modified_files:
                            zip_path = temp_dir_path / 'corrected_files.zip'
                            create_zip_from_files(modified_files, zip_path)
                            st.write("🎉 **Process completed successfully!**")
                            
                            # Provide download link for the ZIP file
                            with open(zip_path, "rb") as zip_file:
                                st.download_button(
                                    label="📁 Download corrected files (ZIP)",
                                    data=zip_file,
                                    file_name='corrected_files.zip',
                                    mime="application/zip"
                                )
                    else:
                        st.warning("⚠️ No files with coding extensions were found in the provided directory.")
        
        except Exception as e:
            st.error(f"❌ An error occurred while extracting the ZIP file: {str(e)}")
