import { useState } from "react";
import { View, Text, TextInput, Pressable, StyleSheet } from "react-native";
import { Link, router } from "expo-router";
import { useSession } from "@/auth/SessionContext";

export default function SignUp() {
  const { signUp } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit() {
    setSubmitting(true);
    setError(null);
    const { error: signUpError } = await signUp(email, password);
    setSubmitting(false);
    if (signUpError) {
      setError(signUpError);
      return;
    }
    // GoTrue may require email confirmation depending on the project's Auth settings (not
    // something this client can know or configure) — a session may or may not exist yet.
    setInfo("Account created. If email confirmation is required, confirm it then sign in.");
    router.replace("/(auth)/sign-in");
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>FooFoo</Text>
      <Text style={styles.subtitle}>Create an account</Text>
      <TextInput
        style={styles.input}
        placeholder="Email"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {info ? <Text style={styles.info}>{info}</Text> : null}
      <Pressable style={styles.button} onPress={onSubmit} disabled={submitting}>
        <Text style={styles.buttonText}>{submitting ? "Creating..." : "Sign up"}</Text>
      </Pressable>
      <Link href="/(auth)/sign-in" style={styles.link}>
        <Text>Already have an account? Sign in</Text>
      </Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24, gap: 12 },
  title: { fontSize: 32, fontWeight: "700", textAlign: "center" },
  subtitle: { fontSize: 18, textAlign: "center", marginBottom: 12, color: "#6B6B6B" },
  input: { borderWidth: 1, borderColor: "#D1D1D1", borderRadius: 8, padding: 12 },
  button: { backgroundColor: "#1F7A3F", borderRadius: 8, padding: 14, alignItems: "center" },
  buttonText: { color: "white", fontWeight: "600" },
  error: { color: "#C0392B" },
  info: { color: "#1F7A3F" },
  link: { textAlign: "center", marginTop: 8 },
});
