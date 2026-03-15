import os
import json
import requests
from tavily import TavilyClient
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def scrape_reward_links(url):
    """Scrape link reward từ các website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tìm tất cả link chứa "rewards.coinmaster.com"
        reward_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'rewards.coinmaster.com' in href:
                reward_links.append(href)
        
        # Tìm trong text bằng regex
        text = soup.get_text()
        regex_links = re.findall(r'https://rewards\.coinmaster\.com/[^\s<>"{}|\\^`\[\]]*', text)
        reward_links.extend(regex_links)
        
        return list(set(reward_links))  # Remove duplicates
    except Exception as e:
        print(f"   ⚠️  Scrape error: {str(e)[:50]}")
        return []

def get_last_3_days_spins():
    all_links = {}
    seen_urls = set()

    # Loop over vandaag, gisteren en eergisteren
    for i in range(3):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime("%B %d, %Y")
        # Quay lại tìm từ các blog uy tín (vì rewards.coinmaster.com không public được index)
        query = f"coin master free spins links {date_str}"

        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                include_answer=True,
                max_results=25
            )

            links = []
            print(f"\n🔍 Searching for: {query}")
            print(f"📊 Found {len(response.get('results', []))} results")
            
            for item in response.get("results", []):
                url = item.get("url", "")
                title = item.get("title", "")
                
                # Lấy link từ các website uy tín
                trusted_domains = [
                    "coinmaster-free-spins.net",
                    "lolvvv.com",
                    "pocketgamer.com",
                    "frvr.com",
                    "pockettactics.com",
                    "mycoinmaster.com",
                    "coinmaster-daily.com",
                    "gamersdunia.com",
                    "levvvel.com",
                    "rezortricks.com",
                    "reddit.com",
                    "facebook.com"
                ]
                
                if any(domain in url for domain in trusted_domains) and url not in seen_urls:
                    seen_urls.add(url)
                    
                    # 🔥 Scrape để lấy link reward từ trang này
                    reward_links = scrape_reward_links(url)
                    
                    # Chỉ lưu reward links, bỏ qua blog links
                    for reward_url in reward_links[:3]:  # Max 3 per source
                        if reward_url not in seen_urls:
                            seen_urls.add(reward_url)
                            links.append({"reward": "Coin Master Free Spins", "url": reward_url})
                            print(f"   ✅ Reward link: {reward_url}")

            # Scrape trực tiếp levvvel.com (nguồn nhiều link)
            levvvel_url = "https://levvvel.com/coin-master-free-spins-coins/"
            if levvvel_url not in seen_urls:
                seen_urls.add(levvvel_url)
                reward_links = scrape_reward_links(levvvel_url)
                for reward_url in reward_links[:5]:
                    if reward_url not in seen_urls:
                        seen_urls.add(reward_url)
                        links.append({"reward": "Coin Master Free Spins", "url": reward_url})
                        print(f"   ✅ levvvel reward: {reward_url}")

            all_links[date_str] = links[:12]  # max 12 per dag
            print(f"   ✅ Total: {len(links)} reward link!")
        except Exception as e:
            print(f"❌ Error: {e}")
            all_links[date_str] = []

    return {
        "updated": datetime.now().strftime("%B %d, %Y"),
        "days": all_links
    }

# Run & save
data = get_last_3_days_spins()
with open("spins_today.json", "w") as f:
    json.dump(data, f, indent=2)

# Thêm note về link reward chính thức
print("\n" + "="*70)
print("📌 HƯỚNG DẪN: Để lấy link reward chính thức (rewards.coinmaster.com):")
print("   1. Truy cập vào một trong các URL phía trên")
print("   2. Tìm link reward có format: https://rewards.coinmaster.com/rewards/...")
print("   3. Ví dụ: https://rewards.coinmaster.com/rewards/rewards.html?c=pe_FCBBTszdL_20260315")
print("="*70 + "\n")

print(f"Success! Last 3 days links saved → {len(data['days'])} days")
