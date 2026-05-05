# 📊 MS Break Trading Assistant

A lightweight trading assistant that connects TradingView alerts to a real-time dashboard for managing trades, enforcing rules, and improving discipline.

This tool is designed for traders using a **1-minute Market Structure Break (MSB) scalping strategy** with fixed TP/SL and strict daily risk rules.

---

## 🚀 Features

- 📡 Receive TradingView signals via webhook  
- 📈 Display LONG / SHORT trade alerts  
- 🎯 Fixed TP/SL guidance (100 TP / 50 SL)  
- 🧠 Enforce trading rules:
  - Stop after **2 losses**
  - Stop after **1 win**
- 📊 Track wins and losses  
- ⚠️ Visual STOP warning system  
- ☁️ Cloud deployable (Fly.io)

---

## 🧠 Strategy Logic

- Timeframe: **1-minute**
- Market: **Nasdaq (MNQ / US100)**
- Entry: Market Structure Break (MSB)
- Trading Window:
  - First **2 hours** after market open  
  - Ignore first **15-minute manipulation candle**

### Risk Management:
- Take Profit: **+100 points**
- Stop Loss: **-50 points**
- Daily rules:
  - ❌ Stop after 2 losses  
  - ✅ Stop after 1 win  

---

## 🧱 Architecture
