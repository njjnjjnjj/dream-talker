// Base64URL to ArrayBuffer
function bufferDecode(value: string): ArrayBuffer {
  const base64 = value.replace(/-/g, '+').replace(/_/g, '/');
  const pad = base64.length % 4;
  const padded = pad ? base64 + '===='.substring(pad) : base64;
  const s = atob(padded);
  const a = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) {
    a[i] = s.charCodeAt(i);
  }
  return a.buffer;
}

// ArrayBuffer to Base64URL
function bufferEncode(value: ArrayBuffer): string {
  const a = new Uint8Array(value);
  const s = String.fromCharCode.apply(null, a as any);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

// Customized recursive function to decode specific Base64URL fields from the server.
export function decodeServerOptions(options: any): any {
  const newOptions = { ...options };

  if (newOptions.challenge) {
    newOptions.challenge = bufferDecode(newOptions.challenge);
  }
  if (newOptions.user && newOptions.user.id) {
    newOptions.user.id = bufferDecode(newOptions.user.id);
  }
  if (newOptions.excludeCredentials) {
    newOptions.excludeCredentials = newOptions.excludeCredentials.map((cred: any) => ({
      ...cred,
      id: bufferDecode(cred.id),
    }));
  }
   if (newOptions.allowCredentials) {
    newOptions.allowCredentials = newOptions.allowCredentials.map((cred: any) => ({
      ...cred,
      id: bufferDecode(cred.id),
    }));
  }

  return newOptions;
}

// Recursive function to encode ArrayBuffers in an object to Base64URL
export function encodeClientResponse(response: any): any {
  if (typeof response === 'object' && response !== null) {
    if (response instanceof ArrayBuffer) {
      return bufferEncode(response);
    }
    if (response instanceof Array) {
      return response.map(encodeClientResponse);
    }
    const newResponse: { [key: string]: any } = {};
    for (const key in response) {
      newResponse[key] = encodeClientResponse(response[key]);
    }
    return newResponse;
  }
  return response;
}