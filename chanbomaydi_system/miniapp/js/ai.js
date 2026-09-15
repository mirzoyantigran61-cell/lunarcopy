
import {
    initializeApp,
    getApps
} from "https://www.gstatic.com/firebasejs/12.19.0/firebase-app.js";

import {
    getAuth,
    onAuthStateChanged,
    signOut
} from "https://www.gstatic.com/firebasejs/12.19.0/firebase-auth.js";


const firebaseConfig = {
    apiKey: "AIzaSyDVr7YpqYyleoBNpfl1QQc0IMRQRYAIr8M",
    authDomain: "yourtigranmods-papaji-devffsrc.firebaseapp.com",
    databaseURL: "https://yourtigranmods-papaji-devffsrc-default-rtdb.firebaseio.com",
    projectId: "yourtigranmods-papaji-devffsrc",
    storageBucket: "yourtigranmods-papaji-devffsrc.firebasestorage.app",
    messagingSenderId: "190570756810",
    appId: "1:190570756810:web:7839bf4a545c51d7b19233",
    measurementId: "G-729S4RCQK4"
};


const app = getApps().length
    ? getApps()[0]
    : initializeApp(firebaseConfig);

const auth = getAuth(app);


const messages =
    document.getElementById("messages");

const welcome =
    document.getElementById("welcome");

const prompt =
    document.getElementById("prompt");

const sendButton =
    document.getElementById("send");

const logoutButton =
    document.getElementById("logout");


let currentUser = null;
let sending = false;


// ============================================================
// AUTH
// ============================================================

onAuthStateChanged(
    auth,

    (user) => {

        if (!user) {

            window.location.replace(
                "/miniapp/login"
            );

            return;
        }

        currentUser = user;

        prompt.focus();
    }
);


logoutButton.addEventListener(
    "click",

    async () => {

        await signOut(auth);

        window.location.replace(
            "/miniapp/login"
        );
    }
);


// ============================================================
// UI
// ============================================================

function addMessage(
    text,
    type
) {

    if (welcome) {
        welcome.style.display =
            "none";
    }

    const row =
        document.createElement(
            "div"
        );

    row.className =
        `message-row ${type}`;

    const bubble =
        document.createElement(
            "div"
        );

    bubble.className =
        "bubble";

    // textContent специально:
    // ответ AI не исполняется как HTML/JS.
    bubble.textContent =
        text;

    row.appendChild(
        bubble
    );

    messages.appendChild(
        row
    );

    messages.scrollTop =
        messages.scrollHeight;

    return {
        row,
        bubble
    };
}


function addTyping() {

    const item =
        addMessage(
            "TIGRAN AI думает...",
            "ai"
        );

    item.bubble.classList.add(
        "typing"
    );

    return item.row;
}


function resizeTextarea() {

    prompt.style.height =
        "auto";

    prompt.style.height =
        Math.min(
            prompt.scrollHeight,
            150
        ) + "px";
}


prompt.addEventListener(
    "input",
    resizeTextarea
);


// ============================================================
// SEND
// ============================================================

async function sendMessage() {

    if (
        sending ||
        !currentUser
    ) {
        return;
    }

    const text =
        prompt.value.trim();

    if (!text) {
        return;
    }

    sending = true;

    sendButton.disabled =
        true;

    prompt.value = "";

    resizeTextarea();

    addMessage(
        text,
        "user"
    );

    const typing =
        addTyping();

    try {

        const token =
            await currentUser.getIdToken();

        const response =
            await fetch(
                "/api/ai/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`
                    },

                    body: JSON.stringify({
                        message: text
                    })
                }
            );

        let data = {};

        try {
            data =
                await response.json();
        } catch (_) {
            data = {};
        }

        typing.remove();

        if (
            !response.ok ||
            !data.ok
        ) {

            if (
                response.status === 401
            ) {

                await signOut(auth);

                window.location.replace(
                    "/miniapp/login"
                );

                return;
            }

            addMessage(
                errorText(
                    data.error
                ),
                "ai"
            );

            return;
        }

        addMessage(
            data.answer ||
            "Не удалось получить ответ.",
            "ai"
        );

    } catch (error) {

        console.error(
            error
        );

        typing.remove();

        addMessage(
            "Ошибка соединения с сервером.",
            "ai"
        );

    } finally {

        sending = false;

        sendButton.disabled =
            false;

        prompt.focus();
    }
}


function errorText(error) {

    switch (error) {

        case "openai_not_configured":

            return (
                "OpenAI API пока не настроен на сервере."
            );

        case "message_too_long":

            return (
                "Сообщение слишком большое."
            );

        case "empty_message":

            return (
                "Сообщение пустое."
            );

        case "firebase_not_configured":

            return (
                "Firebase пока не настроен на сервере."
            );

        case "ai_request_failed":

            return (
                "TIGRAN AI временно не смог обработать запрос."
            );

        default:

            return (
                "Произошла ошибка. Попробуй ещё раз."
            );
    }
}


sendButton.addEventListener(
    "click",
    sendMessage
);


prompt.addEventListener(
    "keydown",

    (event) => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    }
);
