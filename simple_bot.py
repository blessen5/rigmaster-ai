
import re
import random
import urllib.parse
import urllib.request
import json
import ssl
import difflib
import logging
import os

# Configure logging
logging.basicConfig(
    filename='simple_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SimpleBot:
    def __init__(self):
        # 1. DICTIONARY DEFINITIONS (Fast Lookup)
        self.definitions = {
            # Components
            "cpu": "The Central Processing Unit (CPU) is the computer's brain. It handles instructions and calculations. Key specs: Cores, Threads, Clock Speed (GHz).",
            "gpu": "The Graphics Processing Unit (GPU) renders images and video. Essential for gaming and 3D work. Key specs: VRAM (Video Memory), CUDA Cores/Stream Processors.",
            "ram": "Random Access Memory (RAM) is fast, temporary storage for active programs. More RAM = better multitasking. 16GB is standard for gaming.",
            "ssd": "A Solid State Drive (SSD) stores your files permanently. NVMe SSDs are much faster than older SATA SSDs or HDDs. Always boot Windows from an SSD!",
            "hdd": "A Hard Disk Drive (HDD) uses spinning magnetic platters. It's slow and noisy but cheap for massive storage (4TB+).",
            "psu": "The Power Supply Unit (PSU) converts wall power to PC power. Never buy a cheap generic PSU! Look for 80+ Gold certification.",
            "motherboard": "The Motherboard connects all parts together. Ensure the socket (e.g., LGA1700, AM5) matches your CPU.",
            "case": "The Case (Chassis) holds your parts. Good cases have mesh front panels for airflow. Make sure your GPU fits inside!",
            "cooler": "The CPU Cooler keeps the CPU from overheating. Air coolers are reliable; Liquid coolers (AIO) are better for high-end chips.",
            "fan": "Computer fans move air to cool components. PWM fans can control their speed automatically based on temperature.",
            "thermal paste": "Thermal paste fills microscopic gaps between the CPU and Cooler to transfer heat efficiently. Don't forget it!",
            
            # Software & Tech
            "bios": "BIOS/UEFI is the low-level software that starts your PC before Windows loads. You enter it (usually Del/F2) to change settings like XMP/EXPO.",
            "driver": "Drivers are software that tell Windows how to talk to hardware (like your GPU). Always keep GPU drivers updated!",
            "os": "The Operating System (OS) runs your software. Windows 11 is current standard; Linux is great for developers.",
            "bloatware": "Bloatware is pre-installed unwanted software that slows down your PC. It's good practice to remove it.",
            "ray tracing": "Ray Tracing simulates realistic lighting and reflections in games. It's very demanding on the GPU (needs RTX/RX cards).",
            "dlss": "DLSS (Deep Learning Super Sampling) is Nvidia's tech to boost FPS by rendering at low res and AI-upscaling. It's valid magic.",
            "fsr": "FidelityFX Super Resolution (FSR) is AMD's upscaling tech. Works on almost any GPU to boost FPS.",
            "xmp": "XMP (Intel) or EXPO (AMD) are profiles in BIOS to make your RAM run at its advertised speed (e.g., 6000MHz instead of 4800MHz).",
            "overclocking": "Overclocking pushes components (CPU/GPU/RAM) beyond factory speeds for more performance, at the cost of heat and stability.",
            "undervolting": "Undervolting reduces voltage to components to lower heat and power consumption, often maintaining the same performance.",
            "bottleneck": "A bottleneck occurs when one component (e.g., CPU) is too slow for another (e.g., GPU), limiting total performance.",
            "fps": "FPS (Frames Per Second) measures how smooth a game looks. 60 FPS is standard; 144+ FPS is competitive.",
            "resolution": "Resolution is the number of pixels on your screen. 1080p (FHD), 1440p (2K), and 2160p (4K) are common standards.",
            
            # Dev Tools & GitHub
            "git": "Git is a distributed version control system for tracking changes in source code during software development.",
            "github": "GitHub is a developer platform that allows developers to create, store, manage and share their code. It uses Git software.",
            "repo": "A Repository (Repo) contains all of your project's files and each file's revision history.",
            "clone": "`git clone <url>`: Creates a copy of a remote repository on your local machine.",
            "commit": "`git commit -m 'message'` records changes to the repository.",
            "push": "`git push` uploads local repository content to a remote repository.",
            "pull": "`git pull` fetches and merges changes from the remote repository to your working directory.",
            "branch": "Branches allow you to develop features, fix bugs, or safely experiment with new ideas in a contained area of your repository.",
            "merge": "`git merge` joins two or more development histories together.",
            "python": "Python is a high-level, general-purpose programming language. Known for its readability and vast ecosystem.",
            "flask": "Flask is a micro web framework written in Python. It is classified as specific microframework because it does not require particular tools or libraries.",
            "javascript": "JavaScript is the programming language of the Web. It enables dynamic content and interaction on pages.",
            "html": "HTML (HyperText Markup Language) is the standard markup language for documents designed to be displayed in a web browser.",
            "css": "CSS (Cascading Style Sheets) is used for describing the presentation of a document written in a markup language.",

            # General Science & Knowledge
            "gravity": "Gravity is a fundamental interaction which causes mutual attraction between all things that have mass or energy.",
            "light": "Light is electromagnetic radiation that can be perceived by the human eye. Speed of light: ~299,792,458 m/s.",
            "atom": "An atom is the smallest unit of ordinary matter that forms a chemical element. Composed of protons, neutrons, and electrons.",
            "molecule": "A molecule is a group of two or more atoms held together by attractive forces known as chemical bonds.",
            "energy": "Energy is the quantitative property that must be transferred to a body or physical system to perform work on the body, or to heat it.",
            "dna": "DNA (Deoxyribonucleic acid) is a molecule carrying genetic instructions for the development, functioning, growth and reproduction of all known organisms.",
            "evolution": "Evolution is the change in the heritable characteristics of biological populations over successive generations.",
            
            # Brands
            "intel": "Intel makes Core processors (i3, i5, i7, i9). Known for high clock speeds and productivity performance.",
            "amd": "AMD makes Ryzen CPUs and Radeon GPUs. Known for excellent multi-core value and efficiency.",
            "nvidia": "Nvidia makes GeForce RTX GPUs. The market leader for gaming graphics and AI performance.",
            "asus": "ASUS is a top brand for motherboards, GPUs, and monitors. Known for ROG (Republic of Gamers) line.",
            "msi": "MSI is a major manufacturer of motherboards and GPUs. Known for Dragon branding and good mid-range value.",
            "gigabyte": "Gigabyte is a major PC component manufacturer known for AORUS gaming brand.",
            "corsair": "Corsair is famous for RAM, PSUs, Cases, and Peripherals. High quality and good RGB ecosystem (iCUE).",
            "nzxt": "NZXT is known for clean, minimalist cases (H-series) and AIO coolers (Kraken) with LCD screens.",
            "razer": "Razer is a lifestyle brand for gamers, known for RGB peripherals (Chroma) and Blade laptops.",
            "logitech": "Logitech makes industry-leading mice (G502, Superlight) and keyboards. Very reliable.",
            
            # Misc & Fun
            "rgb": "RGB lighting adds customizable colors to your PC. ARGB (Addressable RGB) allows individual LED control.",
            "peripheral": "Peripherals are external devices like Mice, Keyboards, Headsets, and Monitors.",
            "monitor": "A Monitor displays the PC's output. For gaming, look for high Refresh Rate (144Hz+) and low Response Time (1ms).",
            "keyboard": "Mechanical keyboards use physical switches for better feel. 'Red' switches are linear/quiet, 'Blue' are clicky/loud.",
            "mouse": "Gaming mice should have a high-quality sensor and low weight. Wireless is now just as fast as wired.",
            "internet": "A global network of computers. You need Ethernet or Wi-Fi to connect your PC to it.",
            "wifi": "Wi-Fi is a family of wireless network protocols. Wi-Fi 6E/7 provides faster speeds and lower latency.",
            "bluetooth": "Bluetooth is a short-range wireless technology standard that is used for exchanging data between fixed and mobile devices.",
            "42": "The Answer to the Ultimate Question of Life, the Universe, and Everything.",
            "cake": "The cake is a lie."
        }
        
        # 2. LOAD OFFLINE KNOWLEDGE BASE (JSON)
        # This allows for structured Q&A without AI
        self.knowledge_base = []
        kb_path = os.path.join(os.path.dirname(__file__), 'knowledge_base.json')
        if os.path.exists(kb_path):
            try:
                with open(kb_path, 'r') as f:
                    kb_data = json.load(f)
                    self.knowledge_base = kb_data.get('qna', [])
            except Exception as e:
                logging.error(f"Failed to load knowledge_base.json: {e}")

        # 3. MANUAL INTENTS (Conversational Logic)
        self.manual_intents = [
            # Greetings
            (r'\b(hi|hello|hey|greetings|start|yo)\b', ["Hello! Welcome to RigMaster Support.", "Hi! How can I help you build your dream PC?", "Greetings!"]),
            (r'\b(bye|goodbye|exit|quit|pause|later)\b', ["Goodbye! Happy gaming!", "See you next time.", "Safe travels!"]),
            (r'\b(thank|thanks|ty|thankyou)\b', ["You're welcome!", "Anytime!", "Glad to help."]),
            (r'\b(who are you|your name)\b', "I am the **RigMaster Support Bot**. I'm here to help you with PC building and general tech knowledge."),
            
            # Small Talk
            (r'\b(how are you)\b', ["I'm functioning within normal parameters! Ready to assist.", "I'm great! My fans are spinning at optimal speed."]),
            (r'\b(joke|funny)\b', ["Why did the developer go broke? Because he used up all his cache.", "My hardware is getting hot... is it just me or is this build fire?", "I would tell you a UDP joke, but you might not get it."]),

            # Troubleshooting
            (r'\b(slow|lag|freeze|stutter)\b', "### PC Lagging?\n1. check your Temperatures.\n2. Is your SSD full?\n3. Close background apps.\n4. Scan for malware."),
            (r'\b(overheat|hot|temp)\b', "### Overheating?\n- Ensure fans are spinning.\n- Is there dust in the filters?\n- Maybe re-apply thermal paste."),
            (r'\b(bsod|blue screen|crash|error)\b', "### BSOD / Crash?\n- Update your GPU drivers.\n- Update Windows.\n- Reseat your RAM sticks."),
            (r'\b(no display|black screen|no signal)\b', "### No Signal?\n- Plug the monitor into the **GPU**, not the Motherboard.\n- Try a different cable.\n- Reseat the GPU."),
            (r'\b(post|boot|start|won\'t turn on)\b', "### Won't Boot?\n- Check the PSU switch is ON.\n- Look for Debug LEDs on the motherboard.\n- Reseat RAM and GPU.\n- Clear CMOS (remove battery for 5 mins)."),
            
            # Common Store/Site questions
            (r'\b(shipping|delivery|ship|arrive)\b', "We ship worldwide! **Standard**: 5-7 days. **Express**: 2-3 days. Tracking is available in your profile."),
            (r'\b(return|refund|warranty|broken)\b', "All items have a **30-day return policy**. Standard manufacturer warranties apply (usually 2-3 years for major parts)."),
            (r'\b(contact|email|phone|support)\b', "Need a human? Email **support@rigmaster.com** or call **1-800-RIG-MAST**."),
            (r'\b(builder|build page)\b', "Click here to go to the [**PC Builder**](/builder)."),
            (r'\b(analysis|check build)\b', "Click here to go to the [**Analysis Tool**](/analysis)."),
            (r'\b(ai|recommend|architect)\b', "Click here to try the [**AI Architect**](/ai-recommendation)."),
            (r'\b(profile|account|login)\b', "Click here to go to your [**Profile**](/profile)."),

            # Comparisons
            (r'\b(amd|ryzen) vs (intel|core)\b', "**AMD vs Intel**:\n- **AMD (AM5)**: Great efficiency, upgrade path.\n- **Intel (LGA1700)**: High raw performance, but end of platform life."),
            (r'\b(nvidia|rtx) vs (amd|radeon)\b', "**NVIDIA vs AMD**:\n- **NVIDIA**: Better features (DLSS, Ray Tracing), but expensive.\n- **AMD**: Better raw FPS for the money."),
            (r'\b(ddr4) vs (ddr5)\b', "**DDR4 vs DDR5**:\n- **DDR4**: Older, cheaper, good enough for budget builds.\n- **DDR5**: Standard for new builds, much faster, future-proof.")
        ]

    def fetch_duckduckgo_details(self, query):
        """
        Fetches 'Instant Answers' from DuckDuckGo.
        """
        try:
            # Clean query
            clean_query = query.replace('?', '').strip()
            
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_query)}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'RigMasterBot/1.0'})
            
            with urllib.request.urlopen(req, timeout=3) as r:
                data = json.load(r)
                
                # Check for Abstract
                heading = data.get('Heading', '')
                abstract = data.get('AbstractText', '')
                source = data.get('AbstractSource', 'DuckDuckGo')
                url = data.get('AbstractURL', '')
                
                if abstract and len(abstract) > 10:
                    return (
                        f"### {heading} ({source})\n"
                        f"{abstract}\n\n"
                        f"[Read mode]({url})"
                    )
                
                # Check for "Answer"
                answer = data.get('Answer', '')
                if answer:
                     return f"### Quick Answer\n{answer}"
                     
                # Check for "RelatedTopics"
                related = data.get('RelatedTopics', [])
                if related and len(related) > 0:
                    top_result = related[0]
                    if 'Text' in top_result and len(top_result['Text']) > 10:
                        return (
                            f"### {clean_query.title()} (Instant Answer)\n"
                            f"{top_result['Text']}\n"
                            f"[More info]({top_result.get('FirstURL', '#')})"
                        )

        except Exception as e:
            logging.error(f"DDG Error: {e}")
        return None
        
    def fetch_wikipedia_details(self, query):
        """
        Fetches the summary of a topic from Wikipedia.
        """
        try:
            # Strip common question words
            clean_query = re.sub(r'^(what|who|where|how|when|is|are|define|meaning|of|tell me about|difference between|vs)\s+', '', query.lower())
            clean_query = clean_query.replace('?', '').strip()
            
            if len(clean_query) < 2: return None

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            # Search properly
            search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(clean_query)}&limit=1&format=json"
            req_search = urllib.request.Request(search_url, headers={'User-Agent': 'RigMasterBot/1.0'})
            
            best_title = None
            with urllib.request.urlopen(req_search, context=ctx, timeout=3) as r:
                data = json.load(r)
                if len(data) > 1 and len(data[1]) > 0:
                    best_title = data[1][0]
            
            if not best_title:
                return None

            # Fetch Summary
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(best_title)}"
            req_sum = urllib.request.Request(summary_url, headers={'User-Agent': 'RigMasterBot/1.0'})
            
            with urllib.request.urlopen(req_sum, context=ctx, timeout=3) as r:
                data = json.load(r)
                if 'extract' in data:
                    title = data.get('title', best_title)
                    summary = data['extract']
                    page_url = data.get('content_urls', {}).get('desktop', {}).get('page', '#')
                    
                    if "refer to:" in summary:
                        return f"### {title}\nThere are multiple meanings for this. Please be more specific.\n[Read on Wikipedia]({page_url})"

                    return f"### {title} (Wikipedia Result)\n{summary}\n\n[Read full article]({page_url})"
                    
        except Exception as e:
            logging.error(f"Wiki Error: {e}")
        return None

    def fetch_web_search(self, query):
        """
        Performs a general web search via DuckDuckGo and returns top snippets.
        This simulates getting answers from 'any website'.
        """
        try:
            # We use the 'html' version of DDG for snippets if the API is too sparse
            clean_query = query.replace('?', '').strip()
            url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(clean_query)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) RigMaster/1.0'})
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, context=ctx, timeout=4) as r:
                html = r.read().decode('utf-8', errors='ignore')
                
                # Simple extraction of snippets (DDG HTML results are usually in 'result__snippet' class)
                snippets = re.findall(r'<a class="result__snippet".*?>(.*?)</a>', html, re.DOTALL)
                titles = re.findall(r'<a class="result__a".*?>(.*?)</a>', html, re.DOTALL)
                links = re.findall(r'<a class="result__url".*?>(.*?)</a>', html, re.DOTALL)

                if snippets:
                    output = f"### Web Results for '{clean_query.title()}'\n"
                    # Take top 3
                    for i in range(min(3, len(snippets))):
                        title = re.sub('<[^<]+?>', '', titles[i]) if i < len(titles) else "Result"
                        snippet = re.sub('<[^<]+?>', '', snippets[i])
                        link = re.sub('<[^<]+?>', '', links[i]).strip() if i < len(links) else "#"
                        output += f"\n**{i+1}. {title}**\n{snippet}\n[Source](https://{link})\n"
                    return output

        except Exception as e:
            logging.error(f"Web Search Error: {e}")
        return None

    def get_response(self, message):
        """
        Prioritizes INTENT -> MATH -> KB MATCH -> DEFINITION -> DUCKDUCKGO -> WIKIPEDIA -> WEB SEARCH -> FALLBACK.
        """
        message = message.strip()
        msg_lower = message.lower()
        logging.info(f"User: {message}")
        
        # 1. Check Specific Intents (Regex) - Highest Priority
        for pattern, response in self.manual_intents:
            if re.search(pattern, msg_lower):
                if isinstance(response, list):
                    return random.choice(response)
                return response

        # 2. Smart Math Parsing
        possible_math = re.findall(r'[\d.]+\s*[\+\-\*\/]\s*[\d.]+', msg_lower)
        if possible_math:
            try:
                expr = max(possible_math, key=len)
                if any(c in expr for c in "+-*/"):
                    # Use a safe eval-like method if possible, but for now simple eval is okay since we regex filter
                    result = eval(expr)
                    return f"The result of **{expr}** is **{result}**."
            except:
                pass

        # Helper: Is this a complex query that needs fresh web data?
        complex_keywords = {'news', 'latest', 'best', 'review', 'top', '2024', '2025', 'price', 'buy', 'vs', 'update'}
        is_complex = any(k in msg_lower for k in complex_keywords) or len(msg_tokens) > 5

        def lookup_static():
            # 3. Knowledge Base Fuzzy Match
            best_kb_match = None
            highest_score = 0
            for entry in self.knowledge_base:
                score = 0
                for tag in entry['tags']:
                    if tag in msg_tokens: score += 2
                    elif len(tag) > 3 and tag in msg_lower: score += 1
                if score > highest_score:
                    highest_score = score
                    best_kb_match = entry
            if best_kb_match and highest_score > 0:
                 return f"### {best_kb_match['question']}\n{best_kb_match['answer']}"

            # 4. Definition Lookup (Dictionary)
            matches = []
            for token in msg_tokens:
                if token in self.definitions:
                    matches.append(token)
            if matches:
                best_term = max(matches, key=len)
                return f"### {best_term.upper()}\n{self.definitions[best_term]}"
            return None

        # IF NOT COMPLEX: Try static first (Fast)
        if not is_complex:
            static_res = lookup_static()
            if static_res: return static_res

        # 5. DuckDuckGo Instant Answer
        if len(message) > 3:
            ddg_result = self.fetch_duckduckgo_details(msg_lower)
            if ddg_result:
                return ddg_result

        # 6. Wikipedia Fallback
        if len(message) > 2:
            wiki_result = self.fetch_wikipedia_details(msg_lower)
            if wiki_result:
                 return wiki_result

        # 7. General Web Search (Search Google/Websites)
        if len(message) > 4:
            web_result = self.fetch_web_search(msg_lower)
            if web_result:
                return web_result

        # IF COMPLEX: Try static as a last resort before fuzzy
        if is_complex:
            static_res = lookup_static()
            if static_res: return static_res

        # 8. Fuzzy Suggestion
        all_keys = list(self.definitions.keys())
        for entry in self.knowledge_base:
            all_keys.extend(entry['tags'])
        suggestions = difflib.get_close_matches(msg_lower, all_keys, n=3, cutoff=0.6)
        if suggestions:
            sugg_str = ", ".join([f"**{s}**" for s in suggestions])
            return f"I'm not sure about that, but did you mean: {sugg_str}?"

        # 9. Universal Fallback
        return (
            "I couldn't find a direct answer in my database or through a live web search.\n\n"
            "Try asking about:\n"
            "- **Tech**: 'What is Python?', 'Who is Linus Torvalds?'\n"
            "- **Search**: 'Best PC cases 2024', 'Latest CPU news'\n"
            "- **RigMaster**: 'Shipping', 'Returns', 'Warranty'"
        )

# Global instance
simple_bot = SimpleBot()
