import requests

def check_is_short(video_id):
    url = f"https://www.youtube.com/shorts/{video_id}"
    try:
        # Check if it redirects. 
        # Shorts render at /shorts/ID (200 OK)
        # Videos redirect from /shorts/ID to /watch?v=ID (303/302)
        response = requests.head(url, allow_redirects=False, headers={'User-Agent': 'Mozilla/5.0'})
        print(f"ID: {video_id}, Status: {response.status_code}")
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        print(e)
        return False

# Test Cases
# 1. Known Short: "OF9bwurv8WI" (From log: https://www.youtube.com/shorts/OF9bwurv8WI)
# 2. Known Video: "sVS54rBR27Y" (From log: https://www.youtube.com/watch?v=sVS54rBR27Y)

print("Checking Short:")
is_short = check_is_short("OF9bwurv8WI")
print(f"Is Short? {is_short}")

print("\nChecking Video:")
is_video_short = check_is_short("sVS54rBR27Y")
print(f"Is Short? {is_video_short}")
