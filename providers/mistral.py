"""
Log:
- YYYY-MM-DD - [NAME]: Describe the improvement made in this file.
- 2026-10-12 - [Guilherme Silva]: Added the ability to create videos and to play them.
"""

import shutil
import subprocess as standard_subprocess
import json
import os
import pathlib
from pydoc import text
import re
import tempfile
from mistralai.client import Mistral
from dotenv import load_dotenv
from supabase import create_client, Client
import time
from gtts import gTTS #This is for text to speech
from playsound3 import playsound #This is for playing audio
import speech_recognition as sr #This is for speech to text

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def connect_to_supabase():
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    user: dict = supabase.auth.sign_in_with_password({
        'email': USERNAME,
        'password': PASSWORD,
    })
    print("Connected to Supabase:", supabase)
    return supabase

def process_all_pdfs_in_folders():
    input_tokens = 0
    output_tokens = 0
    # Here I will print all the folders inside the "information" folder, and then I will print all the PDFs inside each folder.
    folder = "information"
    path = pathlib.Path(folder)
    prompt = '''Beleive you are the best student ih the world, and you take very complete notes, with all the details, about everything you see at PDF you see, 
        so you will receive a PDF and you will take notes about it, and you will give me the notes in a very complete way, with all the details, 
        so your colleagues can benefit from your notes. Your return should be only notes nothing else, and you should not answer any questions, only take notes.
            On your outputs you shouldn't have things like:
            "**Fim das Notas**
            **Elaborado por:** [Seu Nome] – O Melhor Aluno do Mundo 🌍📚
            **Data:** [Data de Hoje]
            ---
            **Nota**: Estas notas foram elaboradas com **detalhe máximo** para garantir que todos os colegas possam compreender os conceitos de IoT, desde os fundamentos até aplicações avançadas. Se tiverem dúvidas, não hesitem em perguntar! 😊"
        '''
    for e in os.scandir(path):
        if e.is_dir():
            print(f"Folder: {e.name}")
            file_path = pathlib.Path(f"md/{e.name}.md")
            if not file_path.exists():
                for f in os.scandir(e.path):
                    if f.is_file() and f.name.endswith(".pdf"):
                        print(f"\033[91mLet's process the PDF:\033[0m {f.name}")
                        filepath = pathlib.Path(f.path)
                        chat_response = mistral_client.chat.complete(
                            model="mistral-large-2512",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt},
                                        {
                                            "type": "document_url",
                                            "document_url": f"data:application/pdf;base64,{base64.b64encode(filepath.read_bytes()).decode('utf-8')}"
                                        }
                                    ]
                                }
                            ]
                        )
                        print(f"\033[92mNotes for {f.name}:\033[0m")
                        output_text = chat_response.choices[0].message.content
                        print(f"\033[93mTokens used for {f.name}:\033[0m {chat_response.usage.total_tokens}")

                        input_tokens += chat_response.usage.prompt_tokens
                        output_tokens += chat_response.usage.completion_tokens

                        # See if the file was already created, if not create it, if yes, append the new notes to the file.
                        if not os.path.exists(f"md/{e.name}.md"):
                            with open(f"md/{e.name}.md", "w", encoding="utf-8") as f:
                                f.write(f"\n{output_text}")
                                f.close()
                            with open(f"md/{e.name}.md", "r", encoding="utf-8") as f:
                                print(f.read())
                                f.close()
                        else:
                            with open(f"md/{e.name}.md", "a", encoding="utf-8") as f:
                                f.write(f"\n{output_text}")
                                f.close()
                            with open(f"md/{e.name}.md", "r", encoding="utf-8") as f:
                                print(f.read())
                                f.close()
                print(f"\033[92mFinished processing all PDFs in folder {e.name}.\033[0m")
                if not os.path.exists(f"md/{e.name}.md"):
                    print(f"\033[91mNo notes were created for folder {e.name}, skipping index creation.\033[0m")
                else:
                    path = pathlib.Path(f"md/{e.name}.md")
                    if path.exists():   
                        create_index(input_tokens, output_tokens, path)
                    else:
                        print(f"\033[91mThe file md/{e.name}.md does not exist, skipping index creation.\033[0m")
            
            else:
                print(f"\033[93mThe file md/{e.name}.md already exists, skipping the folder.\033[0m")
            
def create_index(input_tokens, output_tokens, path):
    prompt = '''You are a very good student, and you have taken very complete notes about the PDFs you have seen,
            and now you will create an index of all the notes you have taken, and you will return the index in a very complete way, with all the details,
            so your colleagues can benefit from your index, that index should have every single topic the notes contain, and the corresponding page numbers.
                Your return should be only the index nothing else, and you should not answer any questions, only create the index.
                At the end of your index you shoul have somthing like:

                ### **Fim do Índice para este Arquivo**

                This end should be the last line of your index, and you should not have any other text after this line, because this line is very important for 
                the software to know that the index is finished, and that it should not read any other text after this line.

                Here is something that you shouldn't do in your outputs:
                # Index
                - Here is the complete and detailed index of all the notes taken from the PDFs, organized by topic:
                '''

    if not os.path.exists(path):
        print(f"\033[91mThe file {path} does not exist, skipping index creation.\033[0m")
        return

    print(f"\033[92mThe file {path} exists, let's create the index.\033[0m")

    # Read the notes we already have in the file
    with open(path, "r", encoding="utf-8") as f:
        notes_content = f.read()

    print(f"\033[91mLet's build the index for:\033[0m {path}")
    mistral_client = Mistral(api_key=MISTRAL_KEY)
    mistral_response = mistral_client.chat.complete(model="zai-glm-5-2", messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "text", "text": notes_content}
        ]
    }])

    #index_output = chat_response.choices[0].message.content
    index_output = mistral_response.choices[0].message.content
    print(f"\033[92mIndex created for {path}:\033[0m\n{index_output}")
    print(f"\033[93mTokens used for {path}:\033[0m {mistral_response.usage.total_tokens}")

    with open(path, "r+", encoding="utf-8") as f:
        content = f.read()
        f.seek(0, 0)
        f.write(f"# Index\n{index_output}\n\n{content}")

    json_index_all_the_md_files(path)
    total_input_tokens = input_tokens + mistral_response.usage.prompt_tokens
    total_output_tokens = output_tokens + mistral_response.usage.completion_tokens
    input_tokens_cost = total_input_tokens * 0.00000044
    output_tokens_cost = total_output_tokens * 0.0000013
    total_cost = input_tokens_cost + output_tokens_cost
    print(f"\033[93mTotal cost to build {path}:\033[0m ${total_cost:.6f}")

    with open("cost.txt", "a+", encoding="utf-8") as file:
        file.write(f"Total cost to build {path}: ${total_cost:.6f}\n")

# Here you will use your MISTRAL KEY to make questions to the model about your knowledge
def speak_with_model_about_notes(question, option, key):
    topic_doc = "document_index.json"
    path = pathlib.Path(topic_doc)
    mistral_client = Mistral(api_key=key)

    if not os.path.exists(path):
        print(f"\033[91mThe file {topic_doc} does not exist, skipping.\033[0m")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        returned_files = []
        see_file_to_read = '''You will receive a JSON, and that json is like a easier way for you to find the files with the content of the question, 
        you can use how many file you need to answer the question, you only return the files that you will use, 
        and you will not return any other file, and you will return the files in a JSON format, like this:
        {
            "files_used": [
                "file1.md",
                "file2.md"
            ]
        }'''

        # Here you will use the model to find the files to answer the question, and you will return the files in a JSON format
        while True:
            try:
                mistral_response = mistral_client.chat.complete(model="mistral-large-latest", messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": see_file_to_read},
                                {"type": "text", "text": json.dumps(data)},
                                {"type": "text", "text": question}
                            ]
                        }
                    ])
                selection_text = (mistral_response.choices[0].message.content or "").strip()
                if not selection_text:
                    raise ValueError("Model returned empty content (check API key / model name).")
                break
            except Exception as e:
                print(f"\033[91mError: {e}. Retrying...\033[0m")
                time.sleep(1)
                continue

        json_candidate = extract_json_object(selection_text)
        try:
            returned_files = json.loads(json_candidate).get("files_used", [])
        except json.JSONDecodeError:
            returned_files = []

        if not returned_files:
            print(f"\033[91mI only speak about the contents I know.\033[0m")
            exit(1)
        else:
            while True:
                try: 
                    if option == "audio":
                        try:
                            with sr.Microphone() as source:
                                print("Fale agora...")
                                r.adjust_for_ambient_noise(source, duration=1) # type: ignore
                                audio = r.listen(source, timeout=None, phrase_time_limit=None) # type: ignore

                            texto = r.recognize_google(audio, language="pt-PT") # type: ignore
                            print(f"It was said: {texto}")
                            question = texto
                            model_output(prompt, returned_files, question, mistral_client)

                            if texto.lower() in ["exit", "stop"]:
                                exit(0)
                            # Here you will use the gTTS library to convert the text to speech, and then you will play the audio using the playsound library
                            parsed_response = re.sub(r"[*#_`~]", "", mistral_response.choices[0].message.content).strip() # Clean the output for speeching
                            myobj = gTTS(text=parsed_response, lang="pt-PT", slow=False)
                            myobj.save("text_to_speech.mp3")
                            playsound("text_to_speech.mp3")
                            os.remove("text_to_speech.mp3")

                        except sr.UnknownValueError:
                            print("I don't understand. Say again.")
                        except sr.WaitTimeoutError:
                            print("Waiting for you to speak...")
                        except sr.RequestError as e:
                            print(f"Error: {e}")

                    elif option == "text":
                        prompt = '''You are a very good student, and you have taken very complete notes about the PDFs you have seen, you're need see what is the file that contains the notes about the topic 
                            of the question, after that you will answer questions about the notes you have taken, and you will return the answer in a most complete way possible, with all the details,
                            so your colleagues can benefit from your answer, that answer should be based only on the notes you have taken, and not on your own knowledge.
                             You only use the file is attached to the question, and you will answer the question based on the notes in that file, and you will not use any other knowledge you have, 
                            only the notes in the file.
                        '''
                        answer = model_output(prompt, returned_files, question, mistral_client)
                        os.system('cls')
                        print(f"\033[92mAnswer:\033[0m {answer}")
                        input("\033[93mPress Enter to continue...\033[0m")
                        os.system('cls')
                        

                    elif option == "summary":
                        prompt = f'''You are a very good person to do summaries, and you will receive a text, and you will need to create a very good summary of that text, 
                            with the most important points of the text, and you will return the summary'''
                        answer = model_output(prompt, returned_files, question, mistral_client)
                        os.system('cls')
                        print(f"Summary: {answer}")

                    elif option == "quizz":
                        grade = 0
                        prompt = f'''You are a very good person to create quizzes, and you will receive a request, and you will need to create a very good quiz of that request,
                            with the most important points of the content, but never reveal the correct option, I want into a format JSON, like this:
                            [
                                {{
                                    "question": "Question 1",
                                    "options": [
                                        "Option A",
                                        "Option B",
                                        "Option C",
                                        "Option D"
                                    ]
                                }},
                                {{
                                    "question": "Question 2",
                                    "options": [
                                        "Option A",
                                        "Option B",
                                        "Option C",
                                        "Option D"
                                    ]
                                }}
                            ] I only want the JSON, nothing else, and you will not answer any questions, only create the quiz.'''
                        answer = "[" + extract_json_object(model_output(prompt, returned_files, question, mistral_client)) + "]"
                        os.system('cls')
                        try:
                            json_quiz = json.loads(answer)
                            if isinstance(json_quiz, list):
                                for i, q in enumerate(json_quiz):
                                    print(f"\033[92mQuestion {i + 1}:\033[0m {q.get('question')}")
                                    for j, option in enumerate(q.get('options', [])):
                                        print(f"  Option {chr(65 + j)}: {option}") # 65 is the ASCII code for 'A'
                                    while True:
                                        my_answer = input("\033[92mEnter your answer (A, B, C, D): \033[0m").strip().upper()
                                        if my_answer in ['A', 'B', 'C', 'D']:
                                            break
                                        print("\033[91mInvalid option. Please enter A, B, C, or D.\033[0m")
                                    print(f"\033[92mEvaluating your answer...\033[0m")
                                    prompt_check = '''You will need to evaluate the answer of the user, and you will need to tell if the answer is correct or not,
                                      and you will need to give a very complete explanation of the answer. Your is YES or NO, if the answer is NO give me the letter
                                      of the correct option, follow this template:
                                        "correct": "YES" or "NO",
                                        "correct_option": "A" or "B" or "C" or "D".
                                      No explanations, no other text, only the JSON, nothing else, and you will not answer any questions, only evaluate the answer of the user.'''
                                    correction = model_output(prompt_check, returned_files, f"Question: {q.get('question')}, Options: {q.get('options')}, User's answer: {my_answer}", mistral_client)
                                    correction_data = extract_json_object(correction)
                                    correction_json = json.loads(correction_data)
                                    if "YES" in correction:
                                        print(f"\033[92mCorrect! Your answer is right.\033[0m")
                                        grade += 1
                                        input("\033[92mPress Enter to continue to the next question...\033[0m")
                                        os.system('cls')
                                    else:
                                        print(f"\033[91mIncorrect. The correct answer is: {correction_json.get('correct_option')}\033[0m")
                                        input("\033[91mPress Enter to continue to the next question...\033[0m")
                                        os.system('cls')
                            final_grade = (grade / len(json_quiz)) * 100 if json_quiz else 0
                            print(f"\033[92mYour final grade is: {final_grade:.2f}%\033[0m")
                        except json.JSONDecodeError:
                            print(f"\033[91mError: The model did not return a valid JSON for the quiz.\033[0m")
                            print(f"\033[91mModel output:\033[0m {answer}")
                        except Exception as e:
                            print(f"\033[91mUnexpected error: {e}\033[0m")

                    elif option == "flashcards":
                        prompt = f'''You are a very good person to create flashcards, and you will receive a request, and you will need to create a very good flashcards of that request,
                            with the most important points of the content, and you will return the flashcards in a JSON format, like this:
                            [
                                {{
                                    "question": "Question 1",
                                    "answer": "Answer 1"
                                }},
                                {{
                                    "question": "Question 2",
                                    "answer": "Answer 2"
                                }}
                            ] I only want the JSON, nothing else, and you will not answer any questions, only create the flashcards. And 10 flashcards is the maximum you can create, if the content is too big, you will create only 10 flashcards, and you will not create more than 10 flashcards.'''
                        answer = "[" + extract_json_object(model_output(prompt, returned_files, question, mistral_client)) + "]"
                        os.system('cls')
                        try:
                            json_flashcards = json.loads(answer)
                            if isinstance(json_flashcards, list):
                                for i, card in enumerate(json_flashcards):
                                    print(f"\033[92mFlashcard {i + 1}:\033[0m\n")
                                    print(f"Question: {card.get('question')}")
                                    input("\033[93mPress Enter to see the answer...\033[0m")
                                    print(f"Answer: {card.get('answer')}\n")
                                    input("\033[93mPress Enter to continue to the next flashcard...\033[0m")
                                    os.system('cls')
                            else:
                                print(f"\033[91mError: The model did not return a valid JSON for the flashcards.\033[0m")
                        except json.JSONDecodeError:
                            print(f"\033[91mError: The model did not return a valid JSON for the flashcards.\033[0m")
                            print(f"\033[91mModel output:\033[0m {answer}")
                        except Exception as e:
                            print(f"\033[91mUnexpected error: {e}\033[0m")
                        
                    elif option == "video":
                        prompt = """
                            Write a complete, runnable Python script using the Manim Community library
                            (16:9 widescreen layout).

                            Crucial requirements:
                            - Respond ONLY with raw Python code (no explanations and no Markdown fences).
                            - Match the language of the prompt for on-screen text.
                            - Use ONLY Text(...) for typography and labels. NEVER use Tex(...),
                            MathTex(...), or BulletedList(...), because LaTeX is not installed.
                            - Use only standard colors (WHITE, BLACK, BLUE, RED, GREEN, YELLOW, ORANGE,
                            PURPLE, GRAY) or hex strings such as '#2A9D8F'.
                            - When using Code(...), pass ONLY code_string='...' and language='python'.
                            Do not pass style, code_style, font, or font_name arguments.
                            - Write(...) only accepts one vectorized mobject. Use Write(text), Write(line),
                            or another individual VMobject. NEVER call Write(...) with Group(...),
                            VGroup(...), a Python list, or a container of mobjects. To write several
                            mobjects, use LaggedStart(*[Write(item) for item in items]).
                            - Use Group(...) only when a group itself is the target of an operation that
                            supports groups, such as FadeOut(group). Do not reuse that group with Write.
                            - Do not use VGroup(*self.mobjects) for cleanup; use Group(*self.mobjects).
                            - Design every scene for the actual Manim frame. Keep all content
                            inside a safe area with one unit of margin on every side; do not
                            place content at the extreme left or right edges.
                            - Never put a long sentence on one line. Split long text into multiple
                            lines with '\\n', use short bullet points, and use font_size between
                            24 and 40 for body text. A list must fit vertically as well as
                            horizontally; show fewer items per scene when necessary.
                            - Prefer arranging text with VGroup(...).arrange(DOWN, buff=...) and
                            then call group.scale_to_fit_width(config.frame_width - 1)
                            and group.scale_to_fit_height(config.frame_height - 1) when needed.
                        """
                        answer = model_output(prompt, returned_files, question, mistral_client)
                        run_video(answer, quality="l", preview=True)
                        return

                except Exception as e:
                    print(f"\033[91mError: {e}. Retrying...\033[0m")
                    time.sleep(1)
                    continue

def run_video(code_str: str, quality: str = "l", preview: bool = True): # This function was maded by AI but tested several times by a human
    # 1. Strip Markdown fences and non-breaking spaces
    clean = re.sub(r"^```python\s*|^```\s*", "", code_str.strip())
    clean = re.sub(r"```$", "", clean).strip().replace("\xa0", " ")

    # 2. Fix Code(...) argument incompatibilities1
    clean = re.sub(r"\bCode\(\s*code\s*=", "Code(code_string=", clean)
    clean = re.sub(
        r",\s*(?:code_)?style\s*=\s*['\"][^'\"]*['\"]",
        "",
        clean,
    )
    clean = re.sub(
        r"(?:code_)?style\s*=\s*['\"][^'\"]*['\"],\s*",
        "",
        clean,
    )
    clean = re.sub(
        r",\s*font(?:_name)?\s*=\s*['\"][^'\"]*['\"]",
        "",
        clean,
    )
    clean = re.sub(
        r"font(?:_name)?\s*=\s*['\"][^'\"]*['\"],\s*",
        "",
        clean,
    )

    # 3. Replace VGroup(*self.mobjects) with Group(*self.mobjects)
    clean = re.sub(
        r"VGroup\(\s*\*\s*\[([^\]]*self\.mobjects[^\]]*)\]\s*\)",
        r"Group(*[\1])",
        clean,
    )

    # 4. Inject compatibility helpers and responsive text sizing
    fallbacks = (
        "# Auto-injected compatibility helpers\n"
        "try:\n"
        "    ORANGE_E\n"
        "except NameError:\n"
        "    ORANGE_E = interpolate_color(ORANGE, BLACK, 0.5)\n"
        "try:\n"
        "    ORANGE_D\n"
        "except NameError:\n"
        "    ORANGE_D = interpolate_color(ORANGE, BLACK, 0.25)\n"
        "try:\n"
        "    PURPLE_E\n"
        "except NameError:\n"
        "    PURPLE_E = interpolate_color(PURPLE, BLACK, 0.5)\n"
        "try:\n"
        "    LIGHT_PURPLE\n"
        "except NameError:\n"
        "    LIGHT_PURPLE = interpolate_color(PURPLE, WHITE, 0.5)\n\n"
        "class BulletedList(VGroup):\n"
        "    def __init__(self, *items, font_size=28, buff=0.4, **kwargs):\n"
        "        dots_and_text = []\n"
        "        for item in items:\n"
        "            dot = Dot()\n"
        "            txt = Text(\n"
        "                str(item),\n"
        "                font_size=font_size,\n"
        "                **{\n"
        "                    key: value\n"
        "                    for key, value in kwargs.items()\n"
        "                    if key in ['color']\n"
        "                },\n"
        "            )\n"
        "            row = VGroup(dot, txt).arrange(RIGHT, buff=0.2)\n"
        "            dots_and_text.append(row)\n"
        "        super().__init__(*dots_and_text)\n"
        "        self.arrange(DOWN, aligned_edge=LEFT, buff=buff)\n"
        "\n"
        "_OriginalText = Text\n"
        "\n"
        "class _SafeText(_OriginalText):\n"
        "    def __init__(self, *args, **kwargs):\n"
        "        super().__init__(*args, **kwargs)\n"
        "\n"
        "        # Leave one unit of margin on every side of the active frame.\n"
        "        max_width = max(config.frame_width - 1.0, 1.0)\n"
        "        max_height = max(config.frame_height - 1.0, 1.0)\n"
        "\n"
        "        if self.width > max_width:\n"
        "            self.scale_to_fit_width(max_width)\n"
        "\n"
        "        if self.height > max_height:\n"
        "            self.scale_to_fit_height(max_height)\n"
        "\n"
        "Text = _SafeText\n"
    )

    if "from manim import *" in clean:
        clean = clean.replace(
            "from manim import *",
            f"from manim import *\n\n{fallbacks}\n",
            1,
        )
    else:
        clean = f"from manim import *\n\n{fallbacks}\n\n{clean}"

    # 5. Detect the generated Scene class
    match = re.search(
        r"class\s+([A-Za-z0-9_]+)\s*\(\s*Scene\s*\):",
        clean,
    )

    if not match:
        print("\033[91mError:\033[0m Couldn't find a Scene class.")
        return

    scene_name = match.group(1)
    output_folder = os.path.abspath("videos")
    os.makedirs(output_folder, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        script_path = os.path.join(tmp_dir, "scene.py")
        media_path = os.path.join(tmp_dir, "media")

        with open(script_path, "w", encoding="utf-8") as file:
            file.write(clean)

        command = [
            "manim",
            f"-q{quality}",
            "--media_dir",
            media_path,
            script_path,
            scene_name,
        ]

        print(f"\033[94mRendering {scene_name}...\033[0m")

        result = standard_subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            error_output = result.stderr or result.stdout
            print(f"\033[91mManim render failed:\033[0m\n{error_output}")
            return

        temp_video = None

        for root, _, files in os.walk(media_path):
            for file_name in files:
                if file_name.endswith(".mp4"):
                    temp_video = os.path.join(root, file_name)
                    break

            if temp_video:
                break

        if not temp_video:
            print("\033[91mError:\033[0m No video file was generated.")
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        target_name = f"{scene_name}_{timestamp}.mp4"
        saved_video_path = os.path.join(output_folder, target_name)

        shutil.copy2(temp_video, saved_video_path)

        print(f"\033[92mVideo saved to:\033[0m {saved_video_path}")

    print("\033[90mCleaned up intermediate build cache.\033[0m")

    if preview:
        print("\033[94mOpening video...\033[0m")
        os.startfile(saved_video_path)

def model_output(prompt, returned_files, question, mistral_client):
    mistral_response = mistral_client.chat.complete(model="mistral-large-latest", messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "text", "text": json.dumps(returned_files)},
                {"type": "text", "text": question}
            ]
        }
    ])
    return mistral_response.choices[0].message.content

def extract_json_object(text):
    # Prefer a ```json ... ``` fenced block anywhere in the text
    fence_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1)
    fence_match = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1)
    # Fall back to the first { ... last } in the text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text

def ingest_specific_pdf_to_md(mdFile, pdf, mainFolder):
    prompt = '''Beleive you are the best student ih the world, and you take very complete notes, with all the details, about everything you see at PDF you see, 
            so you will receive a PDF and you will take notes about it, and you will give me the notes in a very complete way, with all the details, 
            so your colleagues can benefit from your notes. Your return should be only notes nothing else, and you should not answer any questions, only take notes.
                On your outputs you shouldn't have things like:
                "**Fim das Notas**
                **Elaborado por:** [Seu Nome] – O Melhor Aluno do Mundo 🌍📚
                **Data:** [Data de Hoje]
                ---
                **Nota**: Estas notas foram elaboradas com **detalhe máximo** para garantir que todos os colegas possam compreender os conceitos de IoT, desde os fundamentos até aplicações avançadas. Se tiverem dúvidas, não hesitem em perguntar! 😊"
            '''

    folder_path = pathlib.Path(mainFolder)
    if not os.path.exists(folder_path):
        print(f"\033[91mThe folder {mainFolder} does not exist, skipping.\033[0m")
        return

    target_name = pathlib.Path(pdf).name

    file_path = pathlib.Path(f"md/{mdFile}.md") if not mdFile.endswith(".md") else pathlib.Path(f"md/{mdFile}")

    total_input_tokens = 0
    total_output_tokens = 0
    found = False

    pdf_files = sorted(
        (e for e in os.scandir(folder_path) if e.is_file() and e.name.endswith(".pdf")),
        key=lambda e: e.name
    )

    for f in pdf_files:
        if not found:
            if f.name == target_name:
                found = True
            else:
                print(f"\033[90mSkipping {f.name}, still looking for {target_name}.\033[0m")
                continue

        filepath = pathlib.Path(f.path)
        print(f"\033[91mLet's process the PDF:\033[0m {filepath.name}")

        mistral_response = mistral_client.chat.complete(model="mistral-large-latest", messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "text", "text": json.dumps(pathlib.Path(filepath).read_bytes().decode('latin-1'))},
                    {"type": "text", "text": prompt}
                ]
            }
        ])

        print(f"\033[92mNotes for {filepath.name}:\033[0m")
        output_text = mistral_response.choices[0].message.content
        print(f"\033[93mTokens used for {filepath.name}:\033[0m {mistral_response.usage.total_tokens}")

        total_input_tokens += mistral_response.usage.prompt_tokens
        total_output_tokens += mistral_response.usage.completion_tokens

        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f2:
                f2.write(f"\n{output_text}")
        else:
            with open(file_path, "a", encoding="utf-8") as f2:
                f2.write(f"\n{output_text}")

        with open(file_path, "r", encoding="utf-8") as f2:
            print(f2.read())

        print(f"\033[92mFinished processing {filepath.name} into {file_path}.\033[0m")

    if not found:
        print(f"\033[91mCould not find {target_name} inside {mainFolder}.\033[0m")

    return total_input_tokens, total_output_tokens

def json_index_all_the_md_files(file_path):
    mistral_client = Mistral(api_key=os.getenv("PROVIDER_KEY"))
    subject_name = pathlib.Path(file_path).stem
    prompt = f"""You will receive a md file, and you will create a JSON index of all the notes in that file, and you will return the JSON index in a very complete way,
                with all the details, so your colleagues can benefit from your index.
                The file field must be exactly "{subject_name}". Do not include the .md extension.
                This is your template for the JSON index you will create:
                [
                    {{
                        "file": "{subject_name}",
                        "summary": "Short description of the main content covered in this file",
                        "topics": [
                        "Main topic",
                        "Secondary topic",
                        "Specific concept"
                        ],
                        "keywords": [ # List of relevant keywords or phrases that can help in searching for this file
                        "keyword1",
                        "keyword2",
                        "keyword3",
                        "abbreviation"
                        ]
                    }}
                ]
            """
    mistral_response = mistral_client.chat.complete(model="zai-glm-5-2", messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "text", "text": json.dumps(pathlib.Path(file_path).read_text(encoding="utf-8"))},
            {"type": "text", "text": prompt}
        ]
    }])

    index_path = pathlib.Path("document_index.json")
    try:
        existing_index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.stat().st_size else []
    except (json.JSONDecodeError, FileNotFoundError):
        existing_index = []

    response_text = mistral_response.choices[0].message.content.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1].rsplit("\n", 1)[0]

    new_index = json.loads(response_text)
    if isinstance(new_index, dict):
        new_index = [new_index]
    if not isinstance(new_index, list):
        raise ValueError("The model response must be a JSON object or array.")
    if not isinstance(existing_index, list):
        raise ValueError("document_index.json must contain a JSON array.")

    with index_path.open("w", encoding="utf-8") as f:
        json.dump(existing_index + new_index, f, ensure_ascii=False, indent=2)

    print(f"\033[92mJSON index created for {file_path}:\033[0m\n{new_index}")

'''
def see():
    #Write all the folders and PDFs inside the "information\\CSO" folder, at any depth
    for root, dirs, files in os.walk("information\\CSO"):
        for d in dirs:
            print(f"Folder: {d}")
        for f in files:
            if f.endswith(".pdf"):
                print(f"PDF: {f}")
'''