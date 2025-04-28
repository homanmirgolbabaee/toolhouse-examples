import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

class RedditClient:
    """
    Client for interacting with Reddit's API
    
    This class provides methods to fetch posts, search for content,
    and retrieve detailed information about specific posts without
    requiring authentication (using the public JSON API).
    """
    
    def __init__(self, user_agent: str = None):
        """
        Initialize the Reddit client
        
        Args:
            user_agent: Custom user agent string for API requests
        """
        self.base_url = "https://www.reddit.com"
        self.headers = {
            "User-Agent": user_agent or "RedditAssistant/1.0"
        }
    
    def get_hot_posts(self, subreddit: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get hot posts from a specific subreddit
        
        Args:
            subreddit: Name of the subreddit (without 'r/')
            limit: Maximum number of posts to return
            
        Returns:
            List of post dictionaries containing metadata
        """
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
            print(f"Error fetching posts from r/{subreddit}: {str(e)}")
            return []
    
    def get_new_posts(self, subreddit: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get new posts from a specific subreddit
        
        Args:
            subreddit: Name of the subreddit (without 'r/')
            limit: Maximum number of posts to return
            
        Returns:
            List of post dictionaries containing metadata
        """
        try:
            url = f"{self.base_url}/r/{subreddit}/new.json?limit={limit}"
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
            print(f"Error fetching new posts from r/{subreddit}: {str(e)}")
            return []
    
    def get_top_posts(self, subreddit: str, timeframe: str = "day", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top posts from a specific subreddit
        
        Args:
            subreddit: Name of the subreddit (without 'r/')
            timeframe: Time period for top posts (hour, day, week, month, year, all)
            limit: Maximum number of posts to return
            
        Returns:
            List of post dictionaries containing metadata
        """
        valid_timeframes = ["hour", "day", "week", "month", "year", "all"]
        if timeframe not in valid_timeframes:
            timeframe = "day"  # Default to day if invalid timeframe
            
        try:
            url = f"{self.base_url}/r/{subreddit}/top.json?t={timeframe}&limit={limit}"
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
            print(f"Error fetching top posts from r/{subreddit}: {str(e)}")
            return []
    
    def search_posts(self, query: str, subreddit: str = None, sort: str = "relevance", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for posts across Reddit or within a specific subreddit
        
        Args:
            query: Search query
            subreddit: Optional subreddit to limit search (without 'r/')
            sort: Sort method (relevance, hot, new, top)
            limit: Maximum number of posts to return
            
        Returns:
            List of post dictionaries containing metadata
        """
        try:
            # Build URL based on whether a subreddit is specified
            if subreddit:
                url = f"{self.base_url}/r/{subreddit}/search.json?q={query}&sort={sort}&limit={limit}"
            else:
                url = f"{self.base_url}/search.json?q={query}&sort={sort}&limit={limit}"
                
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
            print(f"Error searching for '{query}': {str(e)}")
            return []
    
    def get_post_details(self, post_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific post including top comments
        
        Args:
            post_url: URL of the Reddit post
            
        Returns:
            Dictionary containing post details and top comments, or None if error
        """
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
            for comment in data[1]['data']['children']:
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
            print(f"Error fetching post details: {str(e)}")
            return None
    
    def get_posts_from_multiple_subreddits(self, subreddits: List[str], post_type: str = "hot", limit_per_sub: int = 3) -> List[Dict[str, Any]]:
        """
        Get posts from multiple subreddits
        
        Args:
            subreddits: List of subreddit names (without 'r/')
            post_type: Type of posts to get (hot, new, top)
            limit_per_sub: Maximum number of posts per subreddit
            
        Returns:
            List of post dictionaries from all specified subreddits
        """
        all_posts = []
        
        for subreddit in subreddits:
            if post_type == "hot":
                posts = self.get_hot_posts(subreddit, limit_per_sub)
            elif post_type == "new":
                posts = self.get_new_posts(subreddit, limit_per_sub)
            elif post_type == "top":
                posts = self.get_top_posts(subreddit, "day", limit_per_sub)
            else:
                posts = self.get_hot_posts(subreddit, limit_per_sub)
                
            all_posts.extend(posts)
            
            # Sleep briefly to avoid hitting rate limits
            time.sleep(0.5)
        
        return all_posts
        
    def format_post_for_display(self, post: Dict[str, Any]) -> str:
        """
        Format a post dictionary into a readable string
        
        Args:
            post: Post dictionary from one of the get_* methods
            
        Returns:
            Formatted string representation of the post
        """
        created_time = datetime.fromtimestamp(post['created_utc']).strftime('%Y-%m-%d %H:%M:%S')
        
        output = f"Title: {post['title']}\n"
        output += f"URL: {post['url']}\n"
        output += f"Subreddit: r/{post['subreddit']}\n"
        output += f"Author: u/{post['author']}\n"
        output += f"Score: {post['score']} | Comments: {post['num_comments']} | Posted: {created_time}\n"
        
        # Include post content if it's a text post
        if post.get('is_self', False) and post.get('selftext', ''):
            # Truncate very long self texts
            selftext = post['selftext']
            if len(selftext) > 500:
                selftext = selftext[:500] + "... [truncated]"
            output += f"Content: {selftext}\n"
        
        # Include top comments if available
        if 'top_comments' in post and post['top_comments']:
            output += "\nTop Comments:\n"
            for i, comment in enumerate(post['top_comments'][:3], 1):  # Show only top 3 comments
                output += f"{i}. u/{comment['author']} (Score: {comment['score']}): "
                
                # Truncate long comments
                comment_body = comment['body']
                if len(comment_body) > 200:
                    comment_body = comment_body[:200] + "..."
                    
                output += f"{comment_body}\n"
        
        return output


# Example usage
if __name__ == "__main__":
    # Simple test code to demonstrate usage
    client = RedditClient()
    
    # Get hot posts from a subreddit
    print("Hot posts from r/Python:")
    posts = client.get_hot_posts("Python", 2)
    for post in posts:
        print(client.format_post_for_display(post))
        print("---")
    
    # Search for posts
    print("\nSearch results for 'machine learning':")
    results = client.search_posts("machine learning", limit=2)
    for result in results:
        print(client.format_post_for_display(result))
        print("---")