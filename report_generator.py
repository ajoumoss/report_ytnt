import datetime

def generate_report(videos):
    """
    Generates a Markdown report from a list of video objects (which include summaries).
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"# YouTube Political Update Report\n"
    report += f"**Generated:** {now}\n\n"
    
    if not videos:
        report += "No new videos found in the last 24 hours.\n"
        return report
    
    for i, video in enumerate(videos, 1):
        # Meta Block First
        report += f"<div class='video-meta'>\n"
        
        # Channel Info (Row 1)
        report += f"<div class='channel-info'>"
        if video.get('channel_profile_pic'):
            report += f"<img src='{video['channel_profile_pic']}' class='channel-icon' alt='channel-icon' />"
        report += f"<strong>{video['channel_title']}</strong></div>"
        
        # Date (Row 2) & Classification (Row 3)
        report += f"<div class='meta-details'>"
        try:
            pub_date = datetime.datetime.fromisoformat(video['published'])
            formatted_date = pub_date.strftime("%Y년 %m월 %d일")
        except:
            formatted_date = video['published']
        report += f"{formatted_date}<br>"
        
        # Subscriber & View Count (Row 2.5)
        stats = []
        if video.get('subscriber_count'):
            sub_text = video['subscriber_count']
            if not sub_text.startswith("구독자"):
                sub_text = f"구독자 {sub_text}"
            stats.append(sub_text)
            
        if video.get('view_count'):
            view_text = video['view_count']
            if not view_text.startswith("조회수"):
                view_text = f"조회수 {view_text}"
            stats.append(view_text)
            
        if stats:
            report += f"<span style='color:#6e6e73; font-size:13px;'>{' | '.join(stats)}</span><br>"
        
        if video.get('political_leaning') and video['political_leaning'] != 'Unknown':
             report += f"<span class='classification-label'>{video['political_leaning']}</span>"
        report += "</div>\n"
        report += "</div>\n" # End video-meta

        # Title Second (Right above content)
        report += f"<h2>{video['title']}</h2>\n"

        # Cast & Key Messages Section
        if video.get('cast') and isinstance(video['cast'], list) and len(video['cast']) > 0:
            report += f"<div class='cast-section' style='background-color: #f5f5f7; padding: 15px; border-radius: 12px; margin-bottom: 20px;'>\n"
            report += f"<h3 style='margin-top:0; font-size:17px;'>👥 출연진 및 핵심 메시지</h3>\n"
            report += f"<ul style='margin-bottom:0; padding-left:20px;'>\n"
            for person in video['cast']:
                name = person.get('name', 'Unknown')
                msg = person.get('key_message', '')
                report += f"<li><strong>{name}</strong>: {msg}</li>\n"
            report += f"</ul>\n"
            report += f"</div>\n"

        # Body (Summary)
        report += f"{video.get('summary', 'No summary available.')}\n"
        
        # Link at bottom
        report += f"<div class='link-container' style='margin-top:15px; text-align:left;'>"
        report += f"<a href='{video['link']}' class='more-link'>YouTube에서 보기 &gt;</a>"
        report += f"</div>\n"
        
        report += "<hr>\n\n"
        
    return report

def save_report(report, filename="report.md"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved to {filename}")

if __name__ == "__main__":
    # Test
    videos = [
        {
            'title': 'Test Video',
            'channel_title': 'Test Channel',
            'published': '2023-10-27',
            'link': 'http://youtube.com',
            'summary': 'This is a summary.'
        }
    ]
    print(generate_report(videos))
