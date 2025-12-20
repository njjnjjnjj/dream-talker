<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useLanguage } from '../composables/useLanguage';
import { Moon, Eye, EyeOff, Fingerprint } from 'lucide-vue-next';
import { decodeServerOptions, encodeClientResponse } from '../utils/webauthn';

const { t } = useLanguage();
const router = useRouter();
const accessCode = ref('');
const error = ref('');
const isLoading = ref(false);
const isPasswordVisible = ref(false);
const showBiometricSetup = ref(false);
const biometricError = ref('');
const isBiometricAvailable = ref(false);

onMounted(() => {
  // Check if WebAuthn is supported
  if (window.PublicKeyCredential) {
    isBiometricAvailable.value = true;
  }
});

const handleLogin = async () => {
  if (!accessCode.value) {
    error.value = t.value.login.errors.empty;
    return;
  }
  isLoading.value = true;
  error.value = '';

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ access_code: accessCode.value }),
    });

    if (response.ok) {
      sessionStorage.setItem('access_token', accessCode.value);
      showBiometricSetup.value = true;
    } else if (response.status === 429) {
      error.value = t.value.login.errors.tooManyAttempts;
    } else {
      error.value = t.value.login.errors.failed;
    }
  } catch (err) {
    error.value = t.value.login.errors.unknown;
  } finally {
    isLoading.value = false;
  }
};

const setupBiometrics = async () => {
  if (!navigator.credentials) {
    biometricError.value = t.value.login.errors.biometricNotSupported;
    return;
  }
  isLoading.value = true;
  biometricError.value = '';
  try {
    const optionsResponse = await fetch('/api/webauthn/register/options');
    const options = await optionsResponse.json();
    const decodedOptions = decodeServerOptions(options);
    console.log('Decoded Options:', decodedOptions); // Debugging

    const credential = await navigator.credentials.create({
      publicKey: decodedOptions,
    });

    const encodedCredential = encodeClientResponse(credential);

    // Manually construct a plain object for serialization
    const verificationData = {
      id: encodedCredential.id,
      rawId: encodedCredential.rawId,
      type: encodedCredential.type,
      response: {
        clientDataJSON: encodedCredential.response.clientDataJSON,
        attestationObject: encodedCredential.response.attestationObject,
      },
    };

    const verifyResponse = await fetch('/api/webauthn/register/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ response: verificationData }),
    });

    if (verifyResponse.ok) {
      router.push('/');
    } else {
      biometricError.value = t.value.login.errors.biometricSetupFailed;
    }
  } catch (err) {
    console.error('Biometric setup failed:', err);
    biometricError.value = t.value.login.errors.biometricSetupFailed;
  } finally {
    isLoading.value = false;
  }
};

const handleBiometricLogin = async () => {
  if (!navigator.credentials) {
    error.value = t.value.login.errors.biometricNotSupported;
    return;
  }
  isLoading.value = true;
  error.value = '';
  try {
    const optionsResponse = await fetch('/api/webauthn/login/options');
    const options = await optionsResponse.json();
    const decodedOptions = decodeServerOptions(options);

    const credential = await navigator.credentials.get({
      publicKey: decodedOptions,
    });
    
    const encodedCredential = encodeClientResponse(credential);

    // Manually construct a plain object for serialization
    const verificationData = {
      id: encodedCredential.id,
      rawId: encodedCredential.rawId,
      type: encodedCredential.type,
      response: {
        clientDataJSON: encodedCredential.response.clientDataJSON,
        authenticatorData: encodedCredential.response.authenticatorData,
        signature: encodedCredential.response.signature,
        userHandle: encodedCredential.response.userHandle,
      },
    };

    const verifyResponse = await fetch('/api/webauthn/login/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ response: verificationData }),
    });

    if (verifyResponse.ok) {
        const data = await verifyResponse.json();
        if (data.access_token) {
            sessionStorage.setItem('access_token', data.access_token);
            router.push('/');
        } else {
            error.value = t.value.login.errors.biometricLoginFailed;
        }
    } else {
        error.value = t.value.login.errors.biometricLoginFailed;
    }
  } catch (err) {
    console.error('Biometric login failed:', err);
    error.value = t.value.login.errors.biometricLoginFailed;
  } finally {
    isLoading.value = false;
  }
};

const skipBiometricSetup = () => {
  router.push('/');
};
</script>

<template>
  <div class="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/20 text-white p-4">
    <div class="w-full max-w-xs text-center">
      
      <div class="mb-8 flex justify-center">
        <div class="bg-indigo-600 p-3 rounded-lg text-white shadow-[0_0_15px_rgba(79,70,229,0.5)]">
          <Moon :size="28" fill="currentColor" />
        </div>
      </div>

      <h1 class="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 to-slate-100 mb-2">
        {{ t.login.title }}
      </h1>
      <p class="text-slate-400 mb-8">{{ t.login.subtitle }}</p>

      <!-- Biometric Setup Dialog -->
      <div v-if="showBiometricSetup" class="bg-slate-800 p-6 rounded-lg shadow-lg animate-in fade-in duration-300">
        <h2 class="text-xl font-bold mb-4">{{ t.login.biometric.setupTitle }}</h2>
        <p class="text-slate-400 mb-6">{{ t.login.biometric.setupDescription }}</p>
        <div v-if="biometricError" class="px-4 py-2 text-sm text-center text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg mb-4">
          {{ biometricError }}
        </div>
        <div class="flex flex-col space-y-3">
          <button @click="setupBiometrics" :disabled="isLoading" class="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-all">
            <Fingerprint class="mr-2 h-5 w-5"/>
            <span>{{ isLoading ? t.login.biometric.settingUp : t.login.biometric.enableButton }}</span>
          </button>
          <button @click="skipBiometricSetup" class="w-full text-slate-400 hover:text-white transition-colors text-sm py-2">
            {{ t.login.biometric.skipButton }}
          </button>
        </div>
      </div>

      <!-- Login Form -->
      <form v-else @submit.prevent="handleLogin" class="space-y-4">
        <div class="relative">
          <label for="access-code" class="sr-only">{{ t.login.placeholder }}</label>
          <input
            id="access-code"
            v-model="accessCode"
            :type="isPasswordVisible ? 'text' : 'password'"
            autocomplete="current-password"
            required
            class="w-full pl-4 pr-12 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 text-center text-lg tracking-widest focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
            :placeholder="t.login.placeholder"
          />
          <button
            type="button"
            @click="isPasswordVisible = !isPasswordVisible"
            class="absolute inset-y-0 right-0 flex items-center justify-center h-full w-12 text-slate-500 hover:text-slate-300 transition-colors"
            :aria-label="isPasswordVisible ? 'Hide password' : 'Show password'"
          >
            <Eye v-if="isPasswordVisible" :size="20" />
            <EyeOff v-else :size="20" />
          </button>
        </div>

        <div v-if="error" class="px-4 py-2 text-sm text-center text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg animate-in fade-in duration-300">
          {{ error }}
        </div>

        <div class="pt-2">
          <button
            type="submit"
            :disabled="isLoading"
            class="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <svg v-if="isLoading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ isLoading ? t.login.verifying : t.login.button }}</span>
          </button>
        </div>

        <div v-if="isBiometricAvailable" class="relative pt-4">
          <div class="absolute inset-0 flex items-center" aria-hidden="true">
            <div class="w-full border-t border-slate-700" />
          </div>
          <div class="relative flex justify-center">
            <span class="bg-slate-900 px-2 text-sm text-slate-500">Or</span>
          </div>
        </div>
        
        <div v-if="isBiometricAvailable" class="pt-2">
           <button
            type="button"
            @click="handleBiometricLogin"
            :disabled="isLoading"
            class="w-full flex justify-center py-3 px-4 border border-slate-700 rounded-lg shadow-sm text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Fingerprint class="mr-2 h-5 w-5"/>
            <span>{{ t.login.biometric.loginButton }}</span>
          </button>
        </div>

      </form>
    </div>
  </div>
</template>