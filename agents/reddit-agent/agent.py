import os
import sys
import requests
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from anthropic import Anthropic
from toolhouse import Toolhouse, Provider
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --------------------------------
# Terminal UI Elements
# --------------------------------
class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# ASCII Art for terminal display
REDDIT_ASCII = '''
{bold}{red}  ____           _     _ _ _      _         _     _              _   
 |  _ \\ ___  __| | __| (_) |_   / \\   ___| |__ (_)___ _____ ___| |_ 
 | |_) / _ \\/ _` |/ _` | | __| / _ \\ / __| '_ \\| / __|_  / / _ \\ __|
 |  _ <  __/ (_| | (_| | | |_ / ___ \\ (__| | | | \\__ \\/ /|  __/ |_ 
 |_| \\_\\___|\\__,_|\\__,_|_|\\__/_/   \\_\\___|_| |_|_|___/___|\\___|\\__|{end}
                                                                   
{yellow}Build your karma with AI-powered engagement strategies{end}
'''

# --------------------------------
# Reddit API Client
# --------------------------------
class RedditClient:
    """Client for interacting with Reddit's official API"""
    
    def __init__(self):
        # We'll use the public JSON API which doesn't require authentication
        self.base_url = "https://www.reddit.com"
        self.headers = {
            "User-Agent": "RedditAssistant/1.0 (by /u/YourUsername)"
        }
    
    def get_hot_posts(self, subreddit: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get hot posts from a specific subreddit"""
        try:
            url = f"{self.base_url}/r/{subreddit}/hot.json?limit={limit}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for post in data['data']['children']:
                post_data = post['data']
                # Extract relevant fields
                posts.append({
                    'title': post_data['title'],
                    'url': f"https://www.reddit.com{post_data['permalink']}",
                    'subreddit': post_data['subreddit'],
                    'author': post_data['author'],
                    'score': post_data['score'],
                    'num_comments': post_data['num_comments'],
                    'created_utc': post_data['created_utc'],
                    'selftext': post_data.get('selftext', ''),
                    'is_self': post_data['is_self']
                })
            
            return posts
        
        except Exception as e:
            print(f"{Colors.RED}Error fetching posts from r/{subreddit}: {str(e)}{Colors.ENDC}")
            return []
    
    def search_posts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for posts across Reddit"""
        try:
            url = f"{self.base_url}/search.json?q={query}&sort=hot&limit={limit}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for post in data['data']['children']:
                post_data = post['data']
                posts.append({
                    'title': post_data['title'],
                    'url': f"https://www.reddit.com{post_data['permalink']}",
                    'subreddit': post_data['subreddit'],
                    'author': post_data['author'],
                    'score': post_data['score'],
                    'num_comments': post_data['num_comments'],
                    'created_utc': post_data['created_utc'],
                    'selftext': post_data.get('selftext', ''),
                    'is_self': post_data['is_self']
                })
            
            return posts
        
        except Exception as e:
            print(f"{Colors.RED}Error searching for '{query}': {str(e)}{Colors.ENDC}")
            return []
    
    def get_post_details(self, post_url: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific post"""
        try:
            # Convert URL to API endpoint
            if post_url.endswith('/'):
                api_url = f"{post_url}.json"
            else:
                api_url = f"{post_url}/.json"
                
            response = requests.get(api_url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            post_data = data[0]['data']['children'][0]['data']
            
            # Get top comments
            comments = []
            for comment in data[1]['data']['children'][:5]:  # Get top 5 comments
                if 'body' in comment.get('data', {}):
                    comments.append({
                        'author': comment['data'].get('author', '[deleted]'),
                        'body': comment['data']['body'],
                        'score': comment['data'].get('score', 0)
                    })
            
            return {
                'title': post_data['title'],
                'url': f"https://www.reddit.com{post_data['permalink']}",
                'subreddit': post_data['subreddit'],
                'author': post_data['author'],
                'score': post_data['score'],
                'num_comments': post_data['num_comments'],
                'created_utc': post_data['created_utc'],
                'selftext': post_data.get('selftext', ''),
                'top_comments': comments
            }
            
        except Exception as e:
            print(f"{Colors.RED}Error fetching post details: {str(e)}{Colors.ENDC}")
            return None

# --------------------------------
# Assistant Manager
# --------------------------------
class RedditAssistant:
    """Main class for the Reddit Assistant"""
    
    def __init__(self):
        # Load API keys from environment variables
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.toolhouse_api_key = os.getenv("TOOLHOUSE_API_KEY")
        
        # Check if API keys are available
        if not self.anthropic_api_key or not self.toolhouse_api_key:
            print(f"{Colors.RED}Error: Missing API keys. Please set ANTHROPIC_API_KEY and TOOLHOUSE_API_KEY.{Colors.ENDC}")
            sys.exit(1)
        
        # Initialize clients
        self.client = Anthropic(api_key=self.anthropic_api_key)
        self.th = Toolhouse(api_key=self.toolhouse_api_key, provider=Provider.ANTHROPIC)
        self.reddit = RedditClient()
        
        # Popular subreddits for engagement
        self.popular_subreddits = [
            "LocalLLaMA", "ChatGPT", "MachineLearning", "artificial", 
            "datascience", "programming", "Python", "learnprogramming",
            "AskReddit", "explainlikeimfive", "IAmA", "todayilearned"
        ]
        
        # Message history
        self.messages = []
        self.first_interaction = True
        
        # System prompt
        self.system_message = self._create_system_prompt()
    
    def create_system_prompt() -> str:
        """Create a simplified system prompt focused just on post response generation"""
        return """
    You are the Reddit Engagement Assistant - you help users craft effective responses to Reddit posts that will earn upvotes and start good discussions.

    Your goal is simple:
    1. Analyze each Reddit post provided by the user
    2. Create ONE engaging response for each post that would be likely to get upvotes
    3. Format your output as a clear table showing the post title and your suggested response

    Guidelines for good responses:
    - Keep them concise but substantive (2-3 sentences is often ideal)
    - Be helpful, informative, and authentic
    - Match the tone of the subreddit when appropriate
    - Add value to the conversation rather than just agreeing
    - Ask thoughtful questions or share relevant experiences when appropriate

    Format your output as a markdown table with:
    | Post Title | Suggested Response | Engagement Potential |
    |------------|-------------------|----------------------|
    | Title here | Your response here | High/Medium/Low |

    Focus exclusively on crafting effective responses - no need to use any tools or extra features.
    """
    
    def clear_screen(self):
        """Clear the terminal screen based on OS"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print the app header with ASCII art"""
        print(REDDIT_ASCII.format(
            bold=Colors.BOLD,
            red=Colors.RED,
            yellow=Colors.YELLOW,
            end=Colors.ENDC
        ))
        print(f"{Colors.CYAN}Type {Colors.BOLD}/help{Colors.ENDC}{Colors.CYAN} for command options or {Colors.BOLD}/exit{Colors.ENDC}{Colors.CYAN} to quit{Colors.ENDC}\n")
    
    def print_help(self):
        """Print help information"""
        print(f"\n{Colors.BOLD}{Colors.PURPLE}=== REDDIT ASSISTANT COMMANDS ==={Colors.ENDC}")
        print(f"{Colors.BLUE}Example queries:{Colors.ENDC}")
        print(f"  {Colors.GREEN}• Search for recent hot posts on r/LocalLLaMA and r/ChatGPT{Colors.ENDC}")
        print(f"  {Colors.GREEN}• Draft responses for posts about AI tools{Colors.ENDC}")
        print(f"  {Colors.GREEN}• Email me engagement opportunities from these posts{Colors.ENDC}")
        print(f"  {Colors.GREEN}• What's the best response for this post: [URL]{Colors.ENDC}")
        print()
        print(f"{Colors.BLUE}Commands:{Colors.ENDC}")
        print(f"  {Colors.YELLOW}/hot [subreddit]{Colors.ENDC} - Get hot posts from a subreddit")
        print(f"  {Colors.YELLOW}/search [query]{Colors.ENDC} - Search for posts across Reddit")
        print(f"  {Colors.YELLOW}/help{Colors.ENDC} - Show this help message")
        print(f"  {Colors.YELLOW}/clear{Colors.ENDC} - Clear conversation history")
        print(f"  {Colors.YELLOW}/exit{Colors.ENDC} - Exit the assistant")
        print()
    
    def format_posts_for_context(self, posts: List[Dict[str, Any]]) -> str:
        """Format posts for the context message to Claude"""
        if not posts:
            return "No posts found."
        
        context = "Here are the posts I found on Reddit:\n\n"
        for i, post in enumerate(posts, 1):
            created_time = datetime.fromtimestamp(post['created_utc']).strftime('%Y-%m-%d %H:%M:%S')
            context += f"Post {i}:\n"
            context += f"Title: {post['title']}\n"
            context += f"URL: {post['url']}\n"
            context += f"Subreddit: r/{post['subreddit']}\n"
            context += f"Author: u/{post['author']}\n"
            context += f"Score: {post['score']} | Comments: {post['num_comments']} | Posted: {created_time}\n"
            
            # Include post content if it's a text post
            if post['is_self'] and post['selftext']:
                # Truncate very long self texts
                selftext = post['selftext']
                if len(selftext) > 500:
                    selftext = selftext[:500] + "... [truncated]"
                context += f"Content: {selftext}\n"
            
            context += "\n"
        
        return context
    
    def handle_command(self, command: str) -> bool:
        """Handle special commands, returns True if a command was handled"""
        parts = command.strip().split(' ', 1)
        cmd = parts[0].lower()
        
        if cmd == "/exit" or cmd == "/quit":
            print(f"\n{Colors.YELLOW}Thanks for using Reddit Assistant! Happy karma hunting!{Colors.ENDC}")
            sys.exit(0)
        
        elif cmd == "/help":
            self.print_help()
            return True
        
        elif cmd == "/clear":
            self.messages.clear()
            self.clear_screen()
            self.print_header()
            self.first_interaction = True
            return True
        
        elif cmd == "/hot":
            subreddit = parts[1] if len(parts) > 1 else "all"
            print(f"{Colors.CYAN}Fetching hot posts from r/{subreddit}...{Colors.ENDC}")
            posts = self.reddit.get_hot_posts(subreddit)
            
            if posts:
                formatted_posts = self.format_posts_for_context(posts)
                self.messages.append({"role": "user", "content": f"I found these hot posts on r/{subreddit}. Can you help me craft engaging responses to increase my karma?\n\n{formatted_posts}"})
                return False  # Continue to process with assistant
            else:
                print(f"{Colors.RED}No posts found in r/{subreddit}.{Colors.ENDC}")
                return True
        
        elif cmd == "/search":
            query = parts[1] if len(parts) > 1 else ""
            if not query:
                print(f"{Colors.RED}Please provide a search query.{Colors.ENDC}")
                return True
                
            print(f"{Colors.CYAN}Searching for posts about '{query}'...{Colors.ENDC}")
            posts = self.reddit.search_posts(query)
            
            if posts:
                formatted_posts = self.format_posts_for_context(posts)
                self.messages.append({"role": "user", "content": f"I found these posts when searching for '{query}'. Can you help me craft engaging responses to increase my karma?\n\n{formatted_posts}"})
                return False  # Continue to process with assistant
            else:
                print(f"{Colors.RED}No posts found for '{query}'.{Colors.ENDC}")
                return True
        
        return False  # Not a command
    
    def process_response(self):
        """Process user input and generate responses"""
        # Show different prompt based on whether it's the first interaction
        if self.first_interaction:
            user_input = input(f"{Colors.BOLD}{Colors.GREEN}How can I help boost your Reddit engagement today? {Colors.ENDC}")
            self.first_interaction = False
        else:
            user_input = input(f"{Colors.BOLD}{Colors.GREEN}What other Reddit assistance do you need? {Colors.ENDC}")
        
        # Handle built-in commands
        if user_input.startswith("/"):
            if self.handle_command(user_input):
                return
        
        # Process regular user input
        else:
            # Try to detect if user input contains a Reddit URL
            if "reddit.com/r/" in user_input and "/comments/" in user_input:
                # Extract URL
                words = user_input.split()
                for word in words:
                    if "reddit.com/r/" in word and "/comments/" in word:
                        url = word.strip('.,!?()"\'')
                        print(f"{Colors.CYAN}Fetching details for the Reddit post...{Colors.ENDC}")
                        post_details = self.reddit.get_post_details(url)
                        
                        if post_details:
                            # Format the post with comments
                            post_info = f"Post Title: {post_details['title']}\n"
                            post_info += f"URL: {post_details['url']}\n"
                            post_info += f"Subreddit: r/{post_details['subreddit']}\n"
                            post_info += f"Author: u/{post_details['author']}\n"
                            post_info += f"Score: {post_details['score']} | Comments: {post_details['num_comments']}\n\n"
                            
                            if post_details['selftext']:
                                post_info += f"Content: {post_details['selftext']}\n\n"
                            
                            if post_details['top_comments']:
                                post_info += "Top Comments:\n"
                                for i, comment in enumerate(post_details['top_comments'], 1):
                                    post_info += f"{i}. u/{comment['author']} (Score: {comment['score']}): {comment['body'][:200]}{'...' if len(comment['body']) > 200 else ''}\n\n"
                            
                            user_input = f"{user_input}\n\nHere are the details of the post:\n\n{post_info}"
            
            # Add user's input to message history
            self.messages.append({"role": "user", "content": user_input})
        
        # Show typing indicator
        print(f"{Colors.CYAN}Analyzing and crafting response...{Colors.ENDC}")
        
        # Generate response using Anthropic model with Toolhouse tools
        response = self.client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2048,
            system=self.system_message,
            # Use Toolhouse tools
            tools=self.th.get_tools(),
            messages=self.messages
        )
        
        # Run tools based on the response
        self.messages += self.th.run_tools(response)
        
        # Generate final response
        agent_setup = self.client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2048,
            system=self.system_message,
            tools=self.th.get_tools(),
            messages=self.messages
        )
        
        agent_reply = agent_setup.content[0].text
        
        # Print AI agent's response
        print(f"\n{Colors.PURPLE}Reddit Assistant:{Colors.ENDC}\n{agent_reply}\n")
        
        # Add AI's response to message history
        self.messages.append({"role": "assistant", "content": agent_reply})
    
    def run(self):
        """Main function to run the Reddit Assistant"""
        self.clear_screen()
        self.print_header()
        
        # Main interaction loop
        while True:
            try:
                self.process_response()
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Exiting Reddit Assistant. Goodbye!{Colors.ENDC}")
                sys.exit(0)
            except Exception as e:
                print(f"{Colors.RED}An error occurred: {str(e)}{Colors.ENDC}")
                continue

# --------------------------------
# Main Entry Point
# --------------------------------
if __name__ == "__main__":
    assistant = RedditAssistant()
    assistant.run()