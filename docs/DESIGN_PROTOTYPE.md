# SRR Chatbot Interface Design Prototype

## Design Overview

This is a modern integrated chatbot interface design developed specifically for the SRR case processing system. The design adopts a unified chat interface where all file processing and information display are integrated into popup modals within the chat area, following modern chat interface design principles.

## Design Specifications

### 🎨 Color System
- **Primary Color**: Purple gradient (#667eea → #764ba2)
- **Background Color**: Light gray (#f8f9fa)
- **Text Color**: Dark gray (#333333)
- **Border Color**: Light gray (#e0e0e0)
- **Success Color**: Green (#28a745)
- **Error Color**: Red (#dc3545)
- **Warning Color**: Orange (#ffc107)

### 📏 Layout Specifications
- **Container Max Width**: 1200px
- **Container Height**: 90vh
- **Border Radius**: 20px (outer), 10px (inner cards)
- **Spacing System**: 8px, 12px, 16px, 20px, 24px
- **Shadow**: 0 20px 40px rgba(0, 0, 0, 0.1)

### 🔤 Typography System
- **Primary Font**: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto'
- **Heading Sizes**: 24px (h1), 18px (h2), 16px (h3)
- **Body Size**: 14px
- **Small Font**: 12px
- **Font Weights**: 400 (normal), 500 (medium), 700 (bold)

## Interface Layout

### 📱 Overall Layout (1200px × 90vh)

```
┌─────────────────────────────────────────────────────────────┐
│                    SRR Case Processing Assistant            │
│                  Intelligent File Processing & Case Query System │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🤖 Hello! I am your SRR Case Processing Assistant...      │
│                                                             │
│  👤 📁 Added file: example.pdf                             │
│                                                             │
│  🤖 ✅ Files added successfully! Total: 1 file.            │
│      Click the "📁 Upload Files" button to view and        │
│      manage your files, or click "Process Files" to start. │
│                                                             │
│  👤 [Process Files]                                         │
│                                                             │
│  🤖 🚀 Starting processing for 1 file...                   │
│                                                             │
│  🤖 ✅ **File Processing Successful!**                     │
│                                                             │
│      📋 **Extracted Case Information:**                     │
│                                                             │
│      📅 **Date Received:** 21-Jan-2025                     │
│      📞 **Source:** TMO                                    │
│      🔢 **Case Number:** 12345                             │
│      ⚡ **Type:** General                                   │
│      👤 **Caller:** John Doe                               │
│      📱 **Contact:** 12345678                              │
│      🏗️ **Slope Number:** 11SW-B/F199                      │
│      📍 **Location:** Example Park                         │
│                                                             │
│      💬 **You can now ask me questions about this case**   │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Ask questions about the case... [📁][⚡][📊][📤]        │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 🗨️ Integrated Chat Area Design

#### Header Section
- **Background**: Purple gradient (#667eea → #764ba2)
- **Text Color**: White
- **Title**: "SRR Case Processing Assistant" (24px, bold)
- **Subtitle**: "Intelligent File Processing & Case Query System" (14px, 90% opacity)
- **Height**: 80px
- **Padding**: 20px
- **Logo**: University and system logos positioned on the left

#### Messages Area
- **Background**: Light gray (#f8f9fa)
- **Scrolling**: Vertical scroll with auto-scroll to bottom
- **Padding**: 20px
- **Min-height**: 0 (essential for flex layout)
- **Max-height**: calc(100vh - 200px)

##### Bot Messages
```
┌─────────────────────────────────────────┐
│ 🤖  ┌─────────────────────────────────┐ │
│     │ Hello! I am your SRR Case       │ │
│     │ Processing Assistant...          │ │
│     │ Please upload PDF or TXT files...│ │
│     └─────────────────────────────────┘ │
└─────────────────────────────────────────┘
```
- **Avatar**: Circular, gray background, bot icon
- **Bubble**: White background, smaller bottom-left radius
- **Border**: 1px light gray
- **Max-width**: 70%
- **Alignment**: Left aligned

##### User Messages
```
┌─────────────────────────────────────────┐
│ ┌─────────────────────────────────┐  👤 │
│ │ What is the basic information   │     │
│ │ of this case?                   │     │
│ └─────────────────────────────────┘     │
└─────────────────────────────────────────┘
```
- **Avatar**: Circular, purple background, user icon
- **Bubble**: Purple gradient background, white text, smaller bottom-right radius
- **Max-width**: 70%
- **Alignment**: Right aligned

#### Input Area with Action Buttons
- **Background**: White
- **Border**: Top 1px light gray border
- **Padding**: 20px
- **Input Field**: Rounded 25px, light gray border, purple border on focus
- **Action Buttons**: Dynamic button system based on application state

##### Button Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Ask questions about the case... [📁][⚡][📊][📤]            │
└─────────────────────────────────────────────────────────────┘
```

##### Button States
- **📁 Upload Files**: Always visible, opens file upload modal
- **⚡ Process Files**: Shows when files are selected but not processed
- **📊 View Details**: Shows when file processing is complete
- **📤 Send Message**: Standard send button for chat queries

### 📁 Modal-Based File Processing Design

#### File Upload Modal
```
┌─────────────────────────────────────────────────────────────┐
│                    File Upload                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              📤                                         │ │
│ │        Click or drag files here                         │ │
│ │         Supports PDF and TXT formats                    │ │
│ │        Maximum file size: 10MB                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Selected Files (2)                          [Clear All] │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ 📄 example.pdf                              [❌]        │ │
│ │ 📄 emailcontent_example.txt                 [❌]        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│                        [Process Files]                      │
└─────────────────────────────────────────────────────────────┘
```

#### File Information Modal
```
┌─────────────────────────────────────────────────────────────┐
│                    File Information                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ File Details                                            │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ 📄 File Name: example.pdf                               │ │
│ │ 📊 File Size: 2.3 MB                                    │ │
│ │ 📋 File Type: application/pdf                            │ │
│ │ ⏱️ Processed At: 2025-01-21 10:30:15                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Processing Status                                       │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ ✅ Text Extraction: 100%                                │ │
│ │ ✅ Data Classification: 95%                             │ │
│ │ ✅ AI Summary: 90%                                      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ AI Summary                                              │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ "Resident reports slope surface cracks requiring       │ │
│ │  immediate inspection and maintenance attention."       │ │
│ │                                                         │ │
│ │ Source: Email Content | Confidence: 0.92               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│                        [Close] [Export JSON]                │
└─────────────────────────────────────────────────────────────┘
```

#### Modal Design Specifications
- **Overlay**: Semi-transparent dark background (rgba(0, 0, 0, 0.5))
- **Modal Size**: Max-width 600px, responsive height
- **Border Radius**: 20px
- **Shadow**: 0 20px 40px rgba(0, 0, 0, 0.3)
- **Animation**: Fade in/out with scale transform
- **Backdrop**: Click to close functionality

### 🎯 Interactive State Design

#### Loading States
- **Loading Animation**: Rotating ring, purple color
- **Text**: "Starting processing for 1 file..." / "Processing..."
- **Location**: Messages area and modal content

#### Success States
- **Color**: Green (#28a745)
- **Icon**: Checkmark icon
- **Message**: "File Processing Successful!"
- **Visual**: Success badges and completion indicators

#### Error States
- **Color**: Red (#dc3545)
- **Icon**: Error icon
- **Message**: Specific error information
- **Visual**: Error alerts with retry options

#### Empty States
- **Text**: "Not provided"
- **Style**: Italic, gray color
- **Background**: Light gray background

#### Button States
- **Default**: Purple gradient background
- **Hover**: Slightly darker purple with scale transform
- **Active**: Pressed state with reduced scale
- **Disabled**: Gray background with reduced opacity

## 📱 Responsive Design

### Mobile Layout (< 768px)
```
┌─────────────────────────┐
│  SRR Case Processing    │
│     Assistant           │
├─────────────────────────┤
│                         │
│      Chat Area          │
│                         │
│ ┌─────────────────────┐ │
│ │ Ask questions...    │ │
│ │ [📁][📤]           │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```
- **Layout**: Single column, full-width chat
- **Modals**: Full-screen on mobile
- **Buttons**: Stacked vertically in input area
- **Typography**: Adjusted font sizes for mobile

### Tablet Layout (768px - 1024px)
- **Layout**: Single integrated chat interface
- **Modals**: Centered with appropriate sizing
- **Touch Targets**: Optimized for touch interaction
- **Typography**: Medium font sizes

### Desktop Layout (> 1024px)
- **Layout**: Full integrated chat interface
- **Modals**: Centered with max-width constraints
- **Hover States**: Enhanced with hover effects
- **Typography**: Full-size fonts

## 🔧 Technical Implementation Details

### CSS Key Features
- **Flexbox Layout**: Flexible responsive layout system
- **CSS Grid**: Information display grids
- **CSS Variables**: Unified design tokens
- **Animations**: Smooth transition effects
- **Media Queries**: Responsive breakpoints
- **Modal System**: Overlay and backdrop management

### Interactive Details
- **Drag & Drop Feedback**: Visual state changes during file upload
- **Button States**: Hover, active, disabled states
- **Input Validation**: Real-time feedback
- **Scroll Behavior**: Smooth scrolling to new messages
- **Loading States**: Prevent duplicate operations
- **Modal Management**: Open/close animations and backdrop handling

### Accessibility
- **Keyboard Navigation**: Full Tab key navigation support
- **Screen Readers**: Semantic HTML structure
- **Color Contrast**: WCAG compliant color schemes
- **Focus Indicators**: Clear focus styles
- **ARIA Labels**: Proper labeling for assistive technologies

### Component Architecture
- **React Components**: Modular component structure
- **TypeScript**: Type-safe component props
- **State Management**: useState for component state
- **Event Handling**: Comprehensive user interaction handling
- **Modal System**: Reusable modal components

## 🎨 Design Files

Since this is a code-implemented design, the following tools are recommended for creating Figma prototypes:

1. **Create Figma Files**
2. **Set up Design System** (colors, fonts, components)
3. **Create Main Interface** (desktop version)
4. **Create Responsive Versions** (mobile version)
5. **Add Interactive Prototypes** (clicks, drag & drop, state changes)
6. **Create Component Library** (buttons, cards, input fields, etc.)

### Figma Component Recommendations
- **Button Components**: Primary, secondary, icon buttons
- **Card Components**: Information cards, file cards
- **Input Components**: Text input, file upload
- **Message Components**: User messages, bot messages
- **Modal Components**: Upload modal, info modal
- **Status Components**: Loading, success, error states

### Key Design Principles
- **Unified Experience**: All functionality within chat interface
- **Intuitive Operations**: Simplified complex operations through modals
- **Information Transparency**: Clear visibility of processing and results
- **User-Friendly Interaction**: Rich visual feedback and operation guidance

This design prototype document provides complete visual specifications and interaction guidelines that can serve as a reference foundation for Figma design implementation.
