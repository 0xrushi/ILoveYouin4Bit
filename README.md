# I Love You in 4-Bit 💘

ILoveYouin4Bit is a playful and experimental app that lets you swipe through dating profiles using Brilliant Labs Frame AR glasses.

Control everything with a joystick, view profiles rendered in charming 4-bit pixel art, and interact while walking your dog, picking up groceries, or just moving through your day

![Alt Text](images/demo.gif)

Android Automation Setup (via Tasker + AutoInput)
To control swiping and screenshots from your Android device, you can set up a local HTTP API using Tasker and the AutoInput plugin.

## Steps:

Install:

[Tasker (paid app)](https://play.google.com/store/apps/details?id=net.dinglisch.android.taskerm&hl=en_us)

[AutoInput (paid app)](https://play.google.com/store/apps/details?id=com.joaomgcd.autoinput&hl=en_US)

**Create an HTTP Server in Tasker**

Set up a Tasker profile that listens for HTTP requests. This will act as a mini local API for swiping/screenshot commands.
👉 Demo: [Tasker HTTP Server Setup](https://youtu.be/0R9Go6tJqKY)

**Configure gesture2.0 Task**

Create a Task in Tasker called gesture2.0 that uses AutoInput to simulate swipe gestures on your screen. Assign this task as the response to HTTP requests.  
👉 Demo: [AutoInput HTTP Swipe Demo](https://youtu.be/qQlPUXw4-_A)

With this setup you can send simple HTTP calls to your phone to do gesture and actions all hands-free