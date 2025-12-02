# Gemini Live API: Transcription Limitations & Streaming Modes

> A comprehensive guide to understanding and solving transcription degradation in long user turns

## Table of Contents

- [Introduction](#introduction)
- [The Problem: Degradation in Long Turns](#the-problem-degradation-in-long-turns)
- [Streaming vs End-of-Speech: A Comparison](#streaming-vs-end-of-speech-a-comparison)
- [The Solution: Periodic Flush Mechanism](#the-solution-periodic-flush-mechanism)
- [Pros and Cons of Each Approach](#pros-and-cons-of-each-approach)
- [Configuration & Best Practices](#configuration--best-practices)
- [Diagnostics & Troubleshooting](#diagnostics--troubleshooting)
- [References](#references)

---

## Introduction

This document addresses a critical challenge when building real-time voice applications with Google's Gemini Live API: **transcription degradation during extended user speech**.

**Audience**: This guide is designed for both developers implementing Gemini Live integrations and technical users configuring and operating voice applications.

**What you'll learn**:
- Why transcriptions degrade or fail after 15+ seconds of continuous speech
- The trade-offs between streaming and batch (end-of-speech) audio delivery
- How the periodic flush mechanism prevents degradation
- How to configure your application for different use cases
- How to diagnose and troubleshoot transcription issues

---

## The Problem: Degradation in Long Turns

### What Happens

When a user speaks continuously for **15+ seconds** without pausing, you may observe:

- Transcriptions that arrive late or not at all
- Degraded or incomplete AI responses
- Audio data accumulating without being processed
- Increased latency in conversation flow

### Why It Occurs

Gemini Live API processes audio in **conversational turns**. A turn begins with an `activity_start` signal and ends with an `activity_end` signal.

**The core issue**: If you stream audio continuously without sending periodic `activity_end` signals, Gemini accumulates the audio in a buffer but doesn't process it until the turn formally ends.

```
User speaks continuously for 30 seconds → Audio accumulates → No processing until activity_end
```

### Timeline of Degradation (Without Flush)

```
Time 0s:   ▶️  activity_start sent
           │   User begins speaking
           │
Time 5s:   │   80 KB accumulated
           │   ✅ Still healthy
           │
Time 10s:  │   160 KB accumulated
           │   ✅ Still healthy
           │
Time 15s:  │   240 KB accumulated
           │   ⚠️  Degradation risk begins
           │
Time 20s:  │   320 KB accumulated
           │   ⚠️  High risk of processing delays
           │
Time 30s:  │   480 KB accumulated
           │   🔴 Likely data loss or severe latency
           │
Time 30s:  ⏹️  activity_end sent
           │   Gemini attempts to process 30s of audio at once
           └── 🐢 Slow or degraded response
```

### Observable Symptoms

**In the User Interface:**
- Transcription text not appearing despite audio being sent
- Turn counter showing yellow (>10 turns) or red (>15 turns)
- Audio visualizer shows activity but no text response

**In Backend Logs:**
```
📊 Audio accumulated: 320KB since last activity_end, 20.5s since activity_start
⚠️  Large audio buffer detected - transcription may be degraded
```

---

## Streaming vs End-of-Speech: A Comparison

The application supports two audio delivery modes, each with distinct characteristics and trade-offs.

### Mode 1: Real-Time Streaming

**How It Works:**

```
1. VAD detects speech → Send activity_start
2. Capture audio continuously in small frames (~32ms chunks)
3. Send each frame immediately over WebSocket
4. VAD detects silence → Send activity_end
```

**Conceptual Implementation:**

```javascript
// Simplified concept - actual code in static/index.html:1334-1337

const FRAME_SIZE_MS = 32;  // milliseconds per audio frame

function onAudioFrame(audioFrame) {
  if (streamingEnabled && isSpeaking) {
    // Convert Float32 PCM to Int16 PCM
    const pcmData = convertToInt16(audioFrame);

    // Send immediately to server
    websocket.send(pcmData);
  }
}
```

**Timing Diagram:**

```
Timeline:
0ms    32ms   64ms   96ms   128ms  ...  Speech End
 │      │      │      │       │            │
 ▼      ▼      ▼      ▼       ▼            ▼
[────][────][────][────][────] ... [────][END]
 Send  Send  Send  Send  Send       Send  ⏹️

Latency: ~32ms between speech and server receipt
```

**Technical Characteristics:**

| Metric | Value |
|--------|-------|
| **Latency** | Low (~32ms per frame) |
| **Network Usage** | High (continuous stream) |
| **Transcription** | Progressive (can arrive in chunks) |
| **Long Turns** | Requires periodic flush |
| **Connection Requirements** | Stable connection preferred |

---

### Mode 2: End-of-Speech (Batch)

**How It Works:**

```
1. VAD detects speech → Send activity_start
2. Capture audio continuously BUT buffer it locally in browser
3. DO NOT send audio frames yet
4. VAD detects silence → Send ALL audio at once + activity_end
```

**Conceptual Implementation:**

```javascript
// Simplified concept - actual code in static/index.html:1290-1296

let audioBuffer = [];

function onAudioFrame(audioFrame) {
  if (!streamingEnabled && isSpeaking) {
    // Store frame locally (don't send yet)
    audioBuffer.push(audioFrame);
  }
}

function onSpeechEnd() {
  // Concatenate all buffered audio
  const completeAudio = concatenate(audioBuffer);

  // Send once as single payload
  const pcmData = convertToInt16(completeAudio);
  websocket.send(pcmData);

  // Always send end signal
  websocket.send({ type: 'activity_end' });

  // Clear buffer for next turn
  audioBuffer = [];
}
```

**Timing Diagram:**

```
Timeline:
0ms    32ms   64ms   96ms   128ms  ...  Speech End
 │      │      │      │       │            │
 ▼      ▼      ▼      ▼       ▼            ▼
[────][────][────][────][────] ... [────][SEND ALL]
 Buffer Buffer Buffer Buffer Buffer    ▶️▶️▶️
                                      Single large
                                       payload

Latency: Speech duration + network transfer time for large payload
```

**Technical Characteristics:**

| Metric | Value |
|--------|-------|
| **Latency** | High (wait until speech ends) |
| **Network Usage** | Low (single transmission) |
| **Transcription** | Arrives all at once (no progressive) |
| **Long Turns** | Large payload (30s speech = ~960 KB) |
| **Connection Requirements** | Works better on unstable connections |

---

### Side-by-Side Comparison

| Aspect | Streaming (Real-Time) | End-of-Speech (Batch) |
|--------|----------------------|----------------------|
| **User Experience** | ✅ Low latency, feels responsive | ❌ High latency, must wait |
| **Network Efficiency** | ⚠️ High bandwidth usage | ✅ Low bandwidth usage |
| **Progressive Transcription** | ✅ Yes - text appears as you speak | ❌ No - text appears after you finish |
| **Long Speech Handling** | ⚠️ Requires periodic flush | ❌ Very large single payload |
| **Unstable Connections** | ❌ May drop frames | ✅ Single reliable transfer |
| **Implementation Complexity** | ⚠️ Requires flush mechanism | ✅ Simpler implementation |
| **Best For** | Interactive conversations | Dictation, transcription services |

---

## The Solution: Periodic Flush Mechanism

The periodic flush mechanism solves the degradation problem in streaming mode by **forcing Gemini to process accumulated audio at regular intervals** without interrupting the user's speech.

### The Concept: "Burst" Signaling

The flush works by sending a rapid sequence of signals:

```
1. Send activity_end    → Force Gemini to process accumulated audio
2. Send activity_start  → Immediately resume listening (no gap in capture)
```

This happens **automatically every 15 seconds** during continuous speech, creating processing "bursts" that keep Gemini responsive.

**Key insight**: The flush is **transparent to the user** - audio capture never stops, only the internal processing boundaries change.

---

### Timeline with Periodic Flush (Every 15s)

```
Time 0s:   ▶️  activity_start (User begins speaking)
           │
Time 5s:   │   80 KB accumulated
           │   ✅ Healthy
           │
Time 10s:  │   160 KB accumulated
           │   ✅ Healthy
           │
Time 15s:  🔄 AUTOMATIC FLUSH
           │   ⏹️  activity_end sent
           │   ▶️  activity_start sent (immediately)
           │   → Gemini processes first 15s chunk
           │   → Buffer resets to 0 KB
           │
Time 20s:  │   80 KB accumulated (new cycle)
           │   ✅ Healthy
           │
Time 25s:  │   160 KB accumulated
           │   ✅ Healthy
           │
Time 30s:  🔄 AUTOMATIC FLUSH
           │   ⏹️  activity_end sent
           │   ▶️  activity_start sent
           │   → Gemini processes second 15s chunk
           │   → Buffer resets to 0 KB
           │
Time 32s:  ⏹️  User stops speaking (VAD detects end)
           │   activity_end sent (final 2s processed)
           └── ✅ Fast, responsive transcription
```

**Result**: Maximum buffer accumulation is ~240 KB instead of 480+ KB, keeping processing responsive.

---

### Conceptual Implementation

```javascript
// Simplified concept - actual code in static/index.html:1212-1226, 1340-1345

const FLUSH_INTERVAL_MS = 15000;  // 15 seconds
let lastFlushTime = null;

// Called on every audio frame (~32ms intervals)
function onAudioFrame(audioFrame) {
  // ... send audio frame if streaming enabled ...

  // Check if flush is needed
  if (flushEnabled && isSpeaking && lastFlushTime) {
    const timeSinceLastFlush = Date.now() - lastFlushTime;

    if (timeSinceLastFlush >= FLUSH_INTERVAL_MS) {
      performPeriodicFlush();
    }
  }
}

function performPeriodicFlush() {
  console.log('Periodic flush triggered at 15s mark');

  // Force processing of accumulated audio
  websocket.send({ type: 'activity_end' });

  // Immediately resume listening (no audio gap)
  websocket.send({ type: 'activity_start' });

  // Reset flush timer
  lastFlushTime = Date.now();
}

// When VAD detects speech start
function onSpeechStart() {
  isSpeaking = true;
  lastFlushTime = Date.now();  // Initialize flush timer
  websocket.send({ type: 'activity_start' });
}

// When VAD detects speech end
function onSpeechEnd() {
  isSpeaking = false;
  lastFlushTime = null;  // Clear flush timer
  websocket.send({ type: 'activity_end' });
}
```

---

### Backend Diagnostic Output

The backend service tracks audio accumulation and logs diagnostic information:

**From `app/services/gemini_live.py` (lines 95-112):**

```python
# Example log output during a flush cycle:

📊 Audio accumulated: 160.0KB since last activity_end, 5.2s since activity_start
▶️  Sent: activity_start (cycle #1)

📊 Audio accumulated: 240.5KB since last activity_end, 15.1s since activity_start
⏹️  Sent: activity_end (duration: 15.1s), audio sent: 240.5KB, cycle #1
▶️  Sent: activity_start (cycle #2)

📊 Audio accumulated: 64.2KB since last activity_end, 4.0s since activity_start
⏹️  Sent: activity_end (duration: 4.0s), audio sent: 64.2KB, cycle #2
```

**What the metrics mean**:
- **Bytes since last activity_end**: Audio accumulation in current cycle
- **Duration since activity_start**: Time elapsed in current turn segment
- **Cycle number**: Count of flush cycles (shows flush is working)

---

## Pros and Cons of Each Approach

### Option 1: Streaming + Periodic Flush (Recommended)

**✅ Advantages:**

- **Low Latency**: Users get near-instant feedback (~32ms frame delay)
- **Progressive Transcription**: Text appears as the user speaks
- **Handles Long Speech**: Flush prevents degradation even in 60s+ turns
- **Better UX**: Feels natural and responsive
- **Real-time Processing**: Gemini processes audio incrementally

**❌ Disadvantages:**

- **Higher Bandwidth**: Continuous stream uses more network data
- **More Complex**: Requires flush logic and VAD integration
- **Configuration Required**: Must tune flush interval for your use case
- **Stable Connection Preferred**: Frame loss possible on poor networks

**🎯 When to Use:**

- Interactive conversations and voice assistants
- Real-time feedback is critical
- User expects immediate responses
- Network connection is stable (Wi-Fi, good cellular)
- Turn length is unpredictable

**Configuration Example:**

```javascript
streamingEnabled = true
flushEnabled = true
FLUSH_INTERVAL_MS = 15000  // Default (tune based on testing)
```

---

### Option 2: End-of-Speech Only (Batch Mode)

**✅ Advantages:**

- **Lower Bandwidth**: Single transmission per turn
- **Simpler Implementation**: No flush mechanism needed
- **Better for Unstable Connections**: One reliable transfer vs many frames
- **Deterministic**: Easier to reason about (one send = one response)

**❌ Disadvantages:**

- **High Perceived Latency**: Must wait until speech ends
- **No Progressive Feedback**: User sees nothing until they finish
- **Large Payloads**: 30s speech = ~960 KB (may hit limits)
- **Poor UX for Conversation**: Feels unnatural for dialogue
- **Potential Timeouts**: Very long turns may exceed WebSocket limits

**🎯 When to Use:**

- Dictation or transcription services (not conversational)
- Network is slow or unstable
- Latency is not a critical concern
- Turns are predictably short (<10s typical)
- Bandwidth is severely constrained

**Configuration Example:**

```javascript
streamingEnabled = false
flushEnabled = false  // Flush doesn't apply in batch mode
```

---

### Option 3: Streaming WITHOUT Flush (Not Recommended)

**🔴 Critical Problems:**

- **Severe Degradation**: Transcriptions fail after 15-20 seconds
- **Data Loss**: Accumulated audio may be dropped
- **Unpredictable Behavior**: Works fine for short turns, fails for long ones
- **Poor User Experience**: Inconsistent performance confuses users

**⚠️ When It Might Work:**

- **Only** if you can **guarantee** user turns are always <10 seconds
- Example: Tightly controlled voice command interface ("play music", "set timer")

**Why It's Risky:**

You can't control how long users speak. A user might ask a complex question or tell a story, hitting the degradation threshold unexpectedly.

**Our Recommendation:** Always enable flush if using streaming mode.

---

## Configuration & Best Practices

### Configuration Parameters

#### Frontend Configuration

**Location**: `static/index.html` (lines 943-958)

```javascript
// Toggleable in Settings Modal
let streamingEnabled = true;   // Real-time streaming vs batch
let flushEnabled = true;       // Periodic flush every 15s

// Flush interval (milliseconds)
const FLUSH_INTERVAL_MS = 15000;  // 15 seconds

// VAD Pre-speech buffer
const PRE_SPEECH_BUFFER_MS = 400;  // Capture 400ms before speech detected
```

#### Backend Configuration

**Location**: `app/config.py`

```python
class Settings(BaseSettings):
    # Audio settings
    audio_sample_rate: int = 16000      # 16 kHz for input
    audio_chunk_size: int = 512         # Samples per frame

    # Flush interval (bytes) - diagnostic tracking
    flush_interval_bytes: int = 160000  # ~5s at 16kHz (diagnostic only)
```

**Note**: The flush interval is controlled by the frontend (`FLUSH_INTERVAL_MS`). The backend `flush_interval_bytes` is for diagnostic logging only.

---

### Recommended Configurations by Use Case

#### Use Case 1: Interactive Voice Assistant

**Scenario**: Natural conversation, unpredictable turn lengths, real-time responses required

```javascript
// Recommended Settings
streamingEnabled = true
flushEnabled = true
FLUSH_INTERVAL_MS = 15000  // Default works well
```

**Why**: Users expect immediate feedback. Flush prevents degradation if they speak at length.

---

#### Use Case 2: Dictation / Transcription Service

**Scenario**: User dictates long-form content, latency is acceptable, transcription accuracy is priority

```javascript
// Recommended Settings
streamingEnabled = false  // Batch mode
flushEnabled = false      // N/A in batch mode
```

**Why**: Batch mode is simpler and more bandwidth-efficient. User is not expecting real-time feedback.

**Alternative** (if progressive transcription is desired):

```javascript
streamingEnabled = true
flushEnabled = true
FLUSH_INTERVAL_MS = 10000  // Shorter interval for more frequent updates
```

---

#### Use Case 3: Unstable Network Connection

**Scenario**: Mobile app on cellular, spotty Wi-Fi, or high-latency connection

```javascript
// Recommended Settings
streamingEnabled = false  // Batch mode more reliable
flushEnabled = false      // N/A in batch mode
```

**Why**: Streaming mode can drop frames on unstable connections. Batch mode ensures complete audio transmission.

---

#### Use Case 4: Voice Commands (Short, Predictable)

**Scenario**: "Alexa-style" commands, always <5 seconds

```javascript
// Option A: Streaming (recommended)
streamingEnabled = true
flushEnabled = true  // Enable as safety net
FLUSH_INTERVAL_MS = 15000  // Won't trigger for short commands

// Option B: Batch (simpler)
streamingEnabled = false
flushEnabled = false
```

**Why**: Both work fine for short turns. Streaming provides lower latency. Batch is simpler if latency is acceptable.

---

### Using the Settings UI

The application includes a settings modal accessible via the ⚙️ button:

```
┌─────────────────────────────────────┐
│         Settings Modal              │
├─────────────────────────────────────┤
│                                     │
│  Real-time streaming         [ON]  │
│  Send audio frames immediately      │
│                                     │
│  Periodic flush (15s)        [ON]  │
│  Prevent degradation in long turns  │
│                                     │
│  Side chat panel            [OFF]  │
│  Toggle chat layout                 │
│                                     │
└─────────────────────────────────────┘
```

**Settings are session-based** (not persisted to localStorage). Refresh the page to reset to defaults.

---

## Diagnostics & Troubleshooting

### Detecting Degradation

#### Frontend Indicators

**1. Turn Counter Color Coding**

Located in the header, the turn counter changes color to warn of potential issues:

```
Turns: 5   → ⚪ White (normal)
Turns: 12  → 🟡 Yellow (warning - consider refresh soon)
Turns: 17  → 🔴 Red (high risk - refresh recommended)
```

**Why it matters**: High turn counts can indicate session fatigue. Refreshing starts a new session.

**2. Missing Transcriptions**

- Audio visualizer shows activity (bars moving)
- No transcription text appears in chat panel
- User hears no response after speaking

**Likely cause**: Flush disabled or degradation occurring

**3. Console Logs**

Open browser DevTools console and look for:

```javascript
Periodic flush: activity_end + activity_start  // Should appear every 15s during speech
Sending 12 pre-speech buffer frames...         // Shows VAD is working
```

---

#### Backend Diagnostic Logs

**Location**: Backend console output (or log files if configured)

**Normal Operation:**

```
📊 Audio accumulated: 160.0KB since last activity_end, 5.2s since activity_start
▶️  Sent: activity_start (cycle #1)
⏹️  Sent: activity_end (duration: 5.2s), audio sent: 160.0KB, cycle #1
```

**Warning Signs:**

```
📊 Audio accumulated: 480.5KB since last activity_end, 30.1s since activity_start
⚠️  Large audio buffer - possible degradation
```

**What to check**:
- **High bytes accumulated** (>300 KB): Flush may be disabled or not triggering
- **Long duration since activity_start** (>20s): Flush should have triggered
- **Low cycle count**: If user spoke for 60s but only 1 cycle logged, flush isn't working

---

### Metrics to Monitor

#### 1. Bytes Accumulated (`_bytes_since_last_activity_end`)

**Backend metric** tracked in `app/services/gemini_live.py`

- **Healthy**: <240 KB (typically <15s of audio)
- **Warning**: 240-400 KB
- **Critical**: >400 KB

**How to check**: Look for `📊 Audio accumulated:` in backend logs

---

#### 2. Duration Since `activity_start` (`_last_activity_start_time`)

**Backend metric** tracked in `app/services/gemini_live.py`

- **Healthy**: <15s (should flush before this)
- **Warning**: 15-25s (flush may have failed)
- **Critical**: >25s (degradation likely)

**How to check**: Look for duration in backend logs: `duration: 15.1s`

---

#### 3. Activity Cycle Count (`_activity_cycles`)

**Backend metric** incremented on each `activity_start`

For a 60-second continuous speech with 15s flush interval:
- **Expected**: 4-5 cycles (0s, 15s, 30s, 45s, end)
- **Problem**: 1 cycle (no flush occurred)

**How to check**: Look for `cycle #N` in backend logs

---

#### 4. Frontend Turn Counter

**UI metric** displayed in header

- **0-9 turns**: Normal (white)
- **10-14 turns**: Warning (yellow) - consider refresh soon
- **15+ turns**: Critical (red) - refresh recommended

**Why**: Gemini sessions can degrade after many turns regardless of flush

---

### Common Problems & Solutions

| Problem | Probable Cause | Solution |
|---------|---------------|----------|
| **Transcriptions lost in long turns** | Flush disabled | Enable flush: `flushEnabled = true` |
| **High latency in responses** | Using end-of-speech mode | Switch to streaming: `streamingEnabled = true` |
| **Connection drops frequently** | Unstable network + streaming | Switch to batch: `streamingEnabled = false` |
| **Turn counter red (>15)** | Long session without refresh | Refresh the page to start new session |
| **Audio visualizer works but no text** | VAD working but Gemini not processing | Check flush is enabled, check backend logs |
| **Very large payloads timing out** | Batch mode + very long speech | Switch to streaming with flush |
| **Inconsistent transcription quality** | Flush disabled or malfunctioning | Verify flush triggers (check console logs every 15s) |

---

### Debug Tools & Techniques

#### Browser Console Debug Commands

Open DevTools Console (F12) and run:

```javascript
// Check current configuration
console.log('Streaming enabled:', streamingEnabled);
console.log('Flush enabled:', flushEnabled);
console.log('Last flush time:', lastFlushTime);
console.log('Currently speaking:', isSpeaking);

// Check VAD status
console.log('VAD instance:', vadInstance);

// Check WebSocket connection
console.log('WebSocket state:', ws?.readyState);
// 0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED
```

#### Backend Log Monitoring

**If running locally:**

```bash
# Watch for audio diagnostics in real-time
uvicorn main:app --reload | grep "Audio accumulated"

# Or with Docker:
docker-compose logs -f app | grep "Audio accumulated"
```

**Look for patterns**:
- Bytes should reset to low values periodically (flush working)
- Duration should never exceed ~17s (accounting for slight delay)
- Cycle count should increment during long speech

---

#### Network Tab Inspection

1. Open DevTools → Network tab
2. Filter by "WS" (WebSocket)
3. Click on the WebSocket connection
4. Switch to "Messages" sub-tab

**What to look for**:
- Green ↑ arrows: Outgoing messages (audio frames, activity signals)
- Red ↓ arrows: Incoming messages (transcriptions, audio responses)

**Healthy pattern** (streaming + flush):
```
↑ {"type":"activity_start"}
↑ Binary (512 bytes)  ← Audio frame
↑ Binary (512 bytes)
↑ Binary (512 bytes)
... (many frames) ...
↑ {"type":"activity_end"}    ← Flush
↑ {"type":"activity_start"}  ← Resume
↑ Binary (512 bytes)
... (continues) ...
```

**Problem pattern** (no flush):
```
↑ {"type":"activity_start"}
↑ Binary (512 bytes)
... (thousands of frames, no activity_end for 30+ seconds) ...
```

---

## References

### Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system architecture, UI components, message protocol
- **[README.md](README.md)** - Quick start guide, installation, basic usage
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines, testing, code quality

### Source Code

#### Frontend Implementation

**File**: `static/index.html`

- **Lines 943-958**: Configuration variables (streaming, flush, intervals)
- **Lines 1212-1226**: Periodic flush logic (`performPeriodicFlush`)
- **Lines 1250-1274**: Speech start handler with pre-speech buffer
- **Lines 1290-1303**: Speech end handler (batch mode audio send)
- **Lines 1334-1337**: Real-time streaming frame sender
- **Lines 1340-1345**: Flush trigger check in frame processor

#### Backend Implementation

**File**: `app/services/gemini_live.py`

- **Lines 43-55**: Gemini API configuration (models, voice, transcription)
- **Lines 84-121**: Audio sender with diagnostic tracking
- **Lines 245-256**: Activity start signal handler
- **Lines 258-283**: Activity end signal with diagnostics and reset

#### WebSocket Handler

**File**: `app/routers/websocket.py`

- **Lines 1-149**: WebSocket endpoint, message routing, session management

### External Resources

- **[Google Gemini Live API Documentation](https://ai.google.dev/)** - Official API reference
- **[Silero VAD](https://github.com/snakers4/silero-vad)** - Voice Activity Detection library used by the application
- **[Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)** - Browser audio processing

---

## Summary

**Key Takeaways**:

1. **The Problem**: Gemini Live API can degrade or fail to process transcriptions during continuous speech >15 seconds if audio accumulates without periodic processing.

2. **Two Modes**:
   - **Streaming (Real-Time)**: Low latency, high bandwidth, requires flush
   - **End-of-Speech (Batch)**: High latency, low bandwidth, simpler

3. **The Solution**: Periodic flush (automatic `activity_end` + `activity_start` every 15s) forces processing during long turns without interrupting capture.

4. **Best Practice**: Use streaming + flush for interactive conversations. Use batch mode only for dictation or when network is unstable.

5. **Monitoring**: Watch backend logs for bytes accumulated, duration since activity_start, and cycle counts. Use frontend turn counter as session health indicator.

**Recommended Default Configuration**:

```javascript
streamingEnabled = true   // Real-time streaming
flushEnabled = true       // Periodic flush every 15s
FLUSH_INTERVAL_MS = 15000 // Default interval
```

This configuration provides the best user experience for conversational AI while preventing degradation in long turns.

---

*This document complements the [ARCHITECTURE.md](ARCHITECTURE.md) guide with specific focus on transcription limitations and streaming strategy. For general system architecture, UI components, and message protocols, see ARCHITECTURE.md.*
