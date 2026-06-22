# 🎬 FreeFlow — Complete Beginner Guide (Hindi + English)

> **Bhai, agar tum bilkul naye ho GitHub aur coding me, tension mat lo!** Ye guide tumhe bilkul ZERO knowledge se lekar full automation tak le jayegi. Har step me screenshot-style instructions hain aur kuch bhi skip nahi karna hai.

---

## 🤔 Ye Kya Hai? (Simple Explanation)

**FreeFlow** ek aisi system hai jo:
1. Tum ek `.md` (Markdown) file doge → wo **automatic video** banayegi (Hindi voice + visuals + subtitles)
2. Ya tum topics ki list doge → wo **har ghante akele** research karke nayi video publish karegi

Sab kuch **FREE** hai, **online** chalta hai, **tumhe koi server rakhne ki zarurat nahi**.

---

## 🎯 Big Picture (Pehle Samjho)

```
📝 Tum likhte ho   →  🤖 System video banata hai  →  📥 Tum download karte ho
   (1 minute)         (5 minute, automatic)          (free, no limit)
```

Ye sab **GitHub** pe chalta hai. GitHub ek website hai jahan code store hota hai. Ye **bilkul free** hai aur tumhara computer se automatically video banati hai — tum sote raho aur videos ban rahi hon!

---

## 📋 Step 0: Things Tumhe Chahiye (Sab Free)

1. ✅ **Ek Gmail/Google account** (Gemini API ke liye) — already hoga shayad
2. ✅ **GitHub account** (free, 2 min me ban jaata hai) — https://github.com/signup
3. ✅ **Internet connection**
4. ✅ **Bas! Aur kuch nahi chahiye**

> ⚠️ Credit card, payment, ya koi paisa ki zarurat NAHI hai.

---

## 🚀 Step 1: GitHub Account Banao (Agar nahi hai)

> GitHub ek website hai jahan tumhara code (ya is case me video pipeline) free me chalti hai.

### 1.1 Sign up
- Browser me jao: **https://github.com/signup**
- Email daalo (Gmail best hai)
- Password banao
- Username choose karo (ye tumhara `username.github.io` banega)
- "Sign up" click karo
- Email verify karo

### 1.2 Ek baar login karo
- **https://github.com** pe jao
- Tumhara profile dikhega

✅ **Done!** GitHub ready hai.

---

## 🔑 Step 2: Google Gemini API Key Banao (Free)

> Gemini = Google ka AI. Ye research aur script likhne ka kaam karega. **1500 videos ki limit per day FREE hai**.

### 2.1 AI Studio pe jao
- Browser me jao: **https://aistudio.google.com**
- "Sign in" pe click karo (apne Gmail se)

### 2.2 API Key banao
- Left side me **"Get API key"** ya **"API Keys"** pe click karo
- "Create API key" button pe click karo
- Ek default project select karo (ya naya banao)
- **API key copy karo** — kuch aisa dikhega: `AIzaSy...` (long string)

### 2.3 Save karo (Notepad me)
- Notepad me paste karo
- Label karo: "GEMINI_API_KEY"
- Ye rakh ke rakhna safe

> ⚠️ **Important**: Ye key private hai. Kisi ko mat dena. Free hai to koi kharid nahi raha.

✅ **Done!** Gemini API key ready.

---

## 🍴 Step 3: FreeFlow Repo Fork Karo (Copy Banao Apne Account Me)

> "Fork" ka matlab hai "copy this project to my account". Iske baad ye project TUMHARE account me chalega.

### 3.1 FreeFlow repo pe jao
- Ye URL kholo (apne browser me): **https://github.com/yourname/freeflow**
  - (Baad me main tumhe exact URL dunga jab ye live ho)

### 3.2 Fork button click karo
- Page ke upar-right me **"Fork"** button dikhega (green/purple color)
- Click karo
- "Create fork" page khulega
- Sab default rakho
- "Create fork" button click karo

### 3.3 Confirm karo
- Tumhare account me ek copy ban gayi
- URL: **https://github.com/TUMHARA-USERNAME/freeflow**

✅ **Done!** Code tumhare paas hai.

---

## 🔐 Step 4: API Keys Ko GitHub Me Save Karo (Secrets)

> "Secrets" ek tarah ka secure locker hai GitHub me. Ye API keys safely store karta hai.

### 4.1 Settings kholo
- Tumhare forked repo me jao: `https://github.com/TUMHARA-USERNAME/freeflow`
- Upar menu me **"Settings"** pe click karo (gear icon)

### 4.2 Secrets section
- Left side menu me **"Secrets and variables"** pe click karo
- Phir **"Actions"** pe click karo

### 4.3 Pehla secret add karo (GEMINI_API_KEY)
- **"New repository secret"** button click karo
- Name: `GEMINI_API_KEY`
- Value: Wo API key paste karo jo Step 2 me copy ki thi
- **"Add secret"** click karo

### 4.4 (Optional) Aur secrets — Filhaal ye skip kar sakte ho
- `GROQ_API_KEY` — optional backup ke liye (https://console.groq.com se free milta hai)
- `PEXELS_API_KEY` — optional stock video ke liye (https://www.pexels.com/api se free)

✅ **Done!** API keys securely store ho gayi.

---

## 🌐 Step 5: GitHub Pages Enable Karo (Free Website)

> GitHub Pages = Free hosting. Tumhari web app `https://TUMHARA-USERNAME.github.io/freeflow` pe live hogi.

### 5.1 Pages settings
- Settings me jao (same as Step 4.1)
- Left side menu me **"Pages"** pe click karo

### 5.2 Source select karo
- "Source" dropdown me **"Deploy from a branch"** select karo
- Branch me **"main"** select karo
- Folder me **"/ (root)"** select karo
- **"Save"** click karo

### 5.3 Wait karo (1-2 min)
- Refresh karo
- Upar message aayega: "Your site is live at..."
- URL: **https://TUMHARA-USERNAME.github.io/freeflow/**

### 5.4 Visit karo
- Browser me wo URL kholo
- Tumhe FreeFlow ka web app dikhega! 🎉

✅ **Done!** Tumhara video pipeline LIVE hai!

---

## 🎬 Mode 1: Pehli Video Banao (MD File Se)

### 6.1 Sample MD download karo
- Apne repo me jao: `https://github.com/TUMHARA-USERNAME/freeflow`
- `examples` folder kholo
- `hindi-script.md` file kholo
- Raw button click karo (upar-right)
- "Ctrl+S" se save karo (ya right-click → "Save as")
- Ya direct: https://raw.githubusercontent.com/yourname/freeflow/main/examples/hindi-script.md

### 6.2 Apni MD file upload karo
- Web app pe jao: `https://TUMHARA-USERNAME.github.io/freeflow`
- **"📄 Mode 1 — MD → Video"** already selected hoga
- Dropzone me apni `.md` file drag & drop karo
  - Ya "Browse Files" click karke select karo
- File dikhai dega with content preview

### 6.3 Settings choose karo
- **Voice**: `hi-IN-Aoede` (Hindi female) selected hoga by default
- **Style Prompt**: Default me "आप एक अनुभवी YouTube narrator हैं..." likha hoga
- **Visual Style**: `Mixed` (stock + AI images) recommended
- **Aspect Ratio**: `16:9` (YouTube) recommended

### 6.4 GitHub PAT (Token) Banao — ONE TIME ONLY
> PAT = Personal Access Token. Ye ek special password hai jo tumhare web app ko GitHub se baat karne deta hai.

1. Naye tab me jao: **https://github.com/settings/tokens**
2. "Generate new token" → **"Generate new token (classic)"** click karo
3. Note: "FreeFlow Web App"
4. Expiration: "No expiration" (ya jitne din chahein)
5. Scopes me **"repo"** check karo (poora select ho jayega)
6. "Generate token" click karo
7. **Token COPY karo** (ye ek baar hi dikhega!) — kuch aisa: `ghp_xxxxx...`
8. Notepad me save karo

### 6.5 Repo name set karo
- Web app pe click karo jab wo pooche "Enter your GitHub repo"
- Type karo: `TUMHARA-USERNAME/freeflow`
- "OK" click karo

### 6.6 Pipeline trigger karo
- Web app me **"🎬 Generate Video"** button pe click karo
- Pehle bolega ki GitHub PAT chahiye — wo paste karo (6.4 wala)
- Status dikhega: "Uploading MD to repo..." → "Starting pipeline..." → "Pipeline running..."
- **2-5 minute wait karo** (page close mat karo!)

### 6.7 Video download karo
- Jab ready hoga, page pe video player dikhega
- "⬇️ Download MP4" pe click karke save karo
- Ya "🔗 Open in new tab" pe click karo

### 6.8 Kahan ja ke videos milti hain?
- Tumhare repo me **"Releases"** section me: `https://github.com/TUMHARA-USERNAME/freeflow/releases`
- Har video ek separate release me upload hoti hai
- Download link direct milta hai

✅ **DONE!** Tumhari pehli video ban gayi! 🎉🎉🎉

---

## 🤖 Mode 2: Auto-Research Channel Set Karo (Har Ghante Video)

> Ye mode me tum topics ki list doge. System har ghante akele research karke video publish karega. Tum sote raho!

### 7.1 Web app me jao
- **https://TUMHARA-USERNAME.github.io/freeflow**
- **"🤖 Mode 2 — Auto-Research Channel"** button pe click karo

### 7.2 Topics add karo
- "Add Topic" field me ek topic type karo (Hindi me ya English me)
  - Example: "भारत के अद्भुत रहस्य जो आप नहीं जानते"
- Category select karo (optional)
- **"➕ Add Topic"** button click karo
- 3-5 topics add karo (zyada bhi add kar sakte ho)

### 7.3 Topics sync karo GitHub me
- "🚀 Generate One Video Now" button click karo
- Topics `pipeline/topics.json` me save ho jayenge GitHub pe
- Aur ek video turant banegi

### 7.4 Hourly schedule ON karo
- Settings check karo
- "Code" → ".github" → "workflows" → "auto-hourly.yml" file kholo
- Line `cron: '5 * * * *'` already hai (ye har ghante run karega)
- Kuch change nahi karna!

### 7.5 Dekh ke raho
- Tumhare repo me "Actions" tab pe jao: `https://github.com/TUMHARA-USERNAME/freeflow/actions`
- Dikhenga ki har ghante ek workflow run hota hai
- Har run me ek video banti hai aur "Releases" me publish hoti hai

✅ **DONE!** Tumhara auto-channel LIVE hai! Har ghante video banegi.

---

## 🛠️ Troubleshooting (Agar Kuch Galat Ho)

### ❌ "GEMINI_API_KEY not set"
- Step 4 dobara check karo. Secret exactly `GEMINI_API_KEY` naam se hona chahiye.

### ❌ "Workflow not found"
- Repo PUBLIC hai? Settings → General → Danger Zone me check karo (free Actions ke liye public zaruri hai)
- Workflow files exist karti hain? `.github/workflows/` folder me dekho

### ❌ "Rate limit exceeded"
- Free tier ki daily limit khatam ho gayi. Kal fir try karo.
- Ya Groq API key bhi add karo (Step 4.4) — backup ke liye

### ❌ "Video generation taking too long"
- Pehli baar 5-10 min lag sakta hai (FFmpeg install hota hai). Baad me 2-3 min me ho jata hai.

### ❌ "404 - Site not found"
- GitHub Pages enable hai? Step 5 dobara karo
- 5-10 min wait karo (deploy hone me time lagta hai)

### ❌ Voice Hindi me nahi aa rahi
- Voice exactly `hi-IN-Aoede` select hai? (case sensitive hai)
- Style prompt me Hindi text hai?

---

## 📚 Common Tasks

### 🎤 Voice Badalna Hai
- Web app me Voice dropdown se koi bhi select karo
- Hindi ke 8 voices hain, English ke 5+

### 📝 Apni Script Likhna Hai
- `examples/hindi-script.md` download karo
- Edit karo Notepad me
- Save as `.md` file
- Web app pe upload karo

### 🎨 Visual Style Change Karna
- **stock**: Sirf Pexels se real videos (no AI images)
- **ai**: Sirf Pollinations se AI generated images
- **mixed**: Dono mix (recommended)

### 📐 Aspect Ratio Badalna
- **16:9**: YouTube videos
- **9:16**: YouTube Shorts, Instagram Reels, TikTok
- **1:1**: Instagram square posts

### 🗣️ Style Prompt Change Karna
- Voice ke niche wale box me apna Hindi tone instruction likho
- Examples:
  - "रोमांचक और उत्साहित अंदाज़ में बोलें"
  - "गंभीर, documentary narrator की तरह"
  - "बच्चों के लिए, simple और fun अंदाज़ में"
  - "Comedy, हास्यपूर्ण अंदाज़ में"

### 🌍 Topics Badalna
- Web app pe Mode 2 me jao
- Old topics delete karo (red Delete button)
- New topics add karo
- "Generate One Video Now" click karo

---

## 🎁 Bonus Tips

1. **First video slow hoga** — FFmpeg download hota hai. Baad me fast hoga.
2. **GitHub Actions tab** check karo regularly: `https://github.com/TUMHARA-USERNAME/freeflow/actions`
3. **Releases tab** me sab videos mil jayengi: `https://github.com/TUMHARA-USERNAME/freeflow/releases`
4. **100 videos tak free me bana sakte ho daily** (Gemini ki 1500 RPD limit me easily)
5. **Mobile pe bhi chalti hai** web app — kisi bhi device pe browser me open karo

---

## 🌟 Advanced: Apna Custom Domain (Optional, Free)

Tum `TUMHARA-USERNAME.github.io/freeflow` ki jagah apna custom domain use kar sakte ho (jaise `myvideos.com`):

1. Free domain lo: **https://www.freenom.com** (ya **https://is-a.dev** se free subdomain)
2. Domain ka DNS me CNAME record add karo: `TUMHARA-USERNAME.github.io`
3. GitHub repo Settings → Pages → Custom domain me apna domain likho
4. Save karo. Done!

---

## 📞 Help Chahiye?

- **GitHub Issues**: `https://github.com/yourname/freeflow/issues` (English me poocho)
- **YouTube tutorials**: Search karo "GitHub Actions tutorial Hindi"
- **Hindi me poocho**: AI tools se poocho (ChatGPT/Gemini), woh tumhe guide karenge

---

## 🎯 Summary Checklist

- [ ] Step 1: GitHub account banaya
- [ ] Step 2: Gemini API key banayi (free)
- [ ] Step 3: FreeFlow repo fork kiya
- [ ] Step 4: API key GitHub Secrets me add ki
- [ ] Step 5: GitHub Pages enable kiya
- [ ] Step 6: Pehli video banayi (MD upload se)
- [ ] Step 7: Auto-research channel set kiya (topics add kiye)
- [ ] BONUS: GitHub Actions tab check kiya
- [ ] BONUS: Releases tab me videos dekhi

✅ Sab done? Congratulations — tum ab **fully automated video channel** ke owner ho!

---

> 🎬 **Yaad rakho**: Sab kuch FREE hai. Agar kabhi koi puche "kya tumhe paisa lag raha hai?" — jawab hai **NAHI, $0/month**. Google ka Gemini AI free hai, GitHub ka hosting free hai, Stock videos free hain, AI images free hain. Ye sab open source tools ke through hota hai.

---

**Questions? Stuck somewhere? Mujhe batao main aur detail me explain karunga!** 🚀
