import { initializeApp } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-app.js";

import {
    getAuth,
    GoogleAuthProvider,
    signInWithPopup,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    sendPasswordResetEmail,
    onAuthStateChanged
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


const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

auth.useDeviceLanguage();


const googleProvider = new GoogleAuthProvider();

googleProvider.setCustomParameters({
    prompt: "select_account"
});


const emailInput =
    document.getElementById("email");

const passwordInput =
    document.getElementById("password");

const loginButton =
    document.getElementById("loginButton");

const registerButton =
    document.getElementById("registerButton");

const resetButton =
    document.getElementById("resetButton");

const googleButton =
    document.getElementById("googleButton");

const statusElement =
    document.getElementById("status");


function showMessage(text, type = "info") {

    if (!statusElement) {
        return;
    }

    statusElement.textContent = text;

    statusElement.className = type;
}


function setLoading(loading) {

    if (loginButton) {
        loginButton.disabled = loading;
    }

    if (registerButton) {
        registerButton.disabled = loading;
    }

    if (resetButton) {
        resetButton.disabled = loading;
    }

    if (googleButton) {
        googleButton.disabled = loading;
    }
}


function friendlyError(error) {

    console.error(error);

    const code = error?.code || "";

    switch (code) {

        case "auth/invalid-email":
            return "Неверный Email.";

        case "auth/missing-password":
            return "Введите пароль.";

        case "auth/invalid-credential":
            return "Неверный Email или пароль.";

        case "auth/email-already-in-use":
            return "Аккаунт с таким Email уже существует.";

        case "auth/weak-password":
            return "Пароль слишком простой.";

        case "auth/popup-closed-by-user":
            return "Окно Google было закрыто.";

        case "auth/popup-blocked":
            return "Браузер заблокировал окно Google.";

        case "auth/unauthorized-domain":
            return "Этот домен не разрешён в Firebase.";

        case "auth/network-request-failed":
            return "Ошибка сети. Проверь подключение.";

        default:
            return error?.message || "Произошла ошибка.";
    }
}


async function goToAI(user) {

    showMessage(
        "Проверяем аккаунт...",
        "info"
    );

    const token =
        await user.getIdToken(true);


    const response =
        await fetch(
            "/api/account/me",
            {
                method: "GET",

                headers: {
                    Authorization:
                        `Bearer ${token}`
                }
            }
        );


    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error(
            "Сервер вернул неправильный ответ."
        );
    }


    if (
        !response.ok ||
        !data.ok
    ) {

        throw new Error(
            data.error ||
            "Server authentication failed"
        );
    }


    showMessage(
        "Готово. Открываем TIGRAN AI...",
        "success"
    );


    window.location.replace(
    "/miniapp"
);
}


// ============================================================
// EMAIL LOGIN
// ============================================================

loginButton?.addEventListener(
    "click",
    async () => {

        const email =
            emailInput?.value.trim();

        const password =
            passwordInput?.value || "";


        if (!email || !password) {

            showMessage(
                "Введите Email и пароль.",
                "error"
            );

            return;
        }


        setLoading(true);

        showMessage(
            "Выполняем вход...",
            "info"
        );


        try {

            const result =
                await signInWithEmailAndPassword(
                    auth,
                    email,
                    password
                );


            await goToAI(
                result.user
            );

        } catch (error) {

            showMessage(
                friendlyError(error),
                "error"
            );

            setLoading(false);
        }
    }
);


// ============================================================
// CREATE ACCOUNT
// ============================================================

registerButton?.addEventListener(
    "click",
    async () => {

        const email =
            emailInput?.value.trim();

        const password =
            passwordInput?.value || "";


        if (!email || !password) {

            showMessage(
                "Введите Email и пароль.",
                "error"
            );

            return;
        }


        if (password.length < 6) {

            showMessage(
                "Пароль должен содержать минимум 6 символов.",
                "error"
            );

            return;
        }


        setLoading(true);

        showMessage(
            "Создаём аккаунт...",
            "info"
        );


        try {

            const result =
                await createUserWithEmailAndPassword(
                    auth,
                    email,
                    password
                );


            await goToAI(
                result.user
            );

        } catch (error) {

            showMessage(
                friendlyError(error),
                "error"
            );

            setLoading(false);
        }
    }
);


// ============================================================
// PASSWORD RESET
// ============================================================

resetButton?.addEventListener(
    "click",
    async () => {

        const email =
            emailInput?.value.trim();


        if (!email) {

            showMessage(
                "Сначала введи Email.",
                "error"
            );

            return;
        }


        setLoading(true);

        try {

            await sendPasswordResetEmail(
                auth,
                email
            );


            showMessage(
                "Письмо для сброса пароля отправлено.",
                "success"
            );

        } catch (error) {

            showMessage(
                friendlyError(error),
                "error"
            );

        } finally {

            setLoading(false);
        }
    }
);


// ============================================================
// GOOGLE
// ============================================================

googleButton?.addEventListener(
    "click",
    async () => {

        setLoading(true);

        showMessage(
            "Открываем Google...",
            "info"
        );


        try {

            const result =
                await signInWithPopup(
                    auth,
                    googleProvider
                );


            await goToAI(
                result.user
            );

        } catch (error) {

            showMessage(
                friendlyError(error),
                "error"
            );

            setLoading(false);
        }
    }
);


// ============================================================
// ENTER = LOGIN
// ============================================================

passwordInput?.addEventListener(
    "keydown",
    event => {

        if (event.key === "Enter") {

            event.preventDefault();

            loginButton?.click();
        }
    }
);


// ============================================================
// EXISTING SESSION
// ============================================================

onAuthStateChanged(
    auth,
    user => {

        console.log(
            user
                ? "Firebase user authenticated"
                : "Firebase user signed out"
        );
    }
);
