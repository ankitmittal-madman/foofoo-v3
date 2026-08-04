import { useState } from "react";
import { View, Text, StyleSheet, Pressable, TextInput, ActivityIndicator, Linking, Alert } from "react-native";
import { useMutation } from "@tanstack/react-query";
import { router } from "expo-router";
import { useSession } from "@/auth/SessionContext";
import { requestExport, pollExport, deleteAccount, REQUIRED_CONFIRMATION_PHRASE } from "@/api/account";
import { describeApiError } from "@/api/errorMessages";

/**
 * Settings tab (P0-2, 2026-08) — the first mobile UI for the DPDP data-subject-rights endpoints
 * (GET /v1/user/export, POST /v1/user/delete). Both Edge Functions were already implemented and
 * fully authorized; neither had a reachable UI entry point before this screen (see
 * docs/active/OPEN_ITEMS.md P0-2 for the evidence). India's DPDP Act requires these rights be
 * user-initiated, so an implemented-but-unreachable backend was a real compliance gap, not just
 * a UX one.
 */
export default function Settings() {
  const { session, signOut } = useSession();
  const userId = session?.user.id;

  return (
    <View testID="settings-screen" style={styles.container}>
      <Text style={styles.header}>Settings</Text>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Preferences</Text>
        <Pressable style={styles.linkButton} onPress={() => router.push("/profile-edit")} testID="settings-profile-edit-link">
          <Text style={styles.linkButtonText}>Edit diet & allergies →</Text>
        </Pressable>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recommendation history</Text>
        <Pressable style={styles.linkButton} onPress={() => router.push("/history")} testID="settings-history-link">
          <Text style={styles.linkButtonText}>View past recommendations →</Text>
        </Pressable>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Your data</Text>
        <Text style={styles.sectionBody}>
          Download a copy of everything FooFoo has stored about your household, preferences, and
          recommendation history.
        </Text>
        <ExportButton />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Delete account</Text>
        <Text style={styles.sectionBody}>
          Permanently deletes your account. This cannot be undone.
        </Text>
        {userId ? <DeleteAccountFlow userId={userId} onDeleted={signOut} /> : null}
      </View>
    </View>
  );
}

function ExportButton() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  const start = useMutation({
    mutationFn: requestExport,
    onSuccess: (res) => {
      setJobId(res.export_job_id);
      if (res.status === "complete" && res.download_url) setDownloadUrl(res.download_url);
    },
  });
  const poll = useMutation({
    mutationFn: (id: string) => pollExport(id),
    onSuccess: (res) => {
      if (res.status === "complete" && res.download_url) setDownloadUrl(res.download_url);
    },
  });

  if (downloadUrl) {
    return (
      <Pressable style={styles.button} onPress={() => Linking.openURL(downloadUrl)}>
        <Text style={styles.buttonLabel}>Download your data</Text>
      </Pressable>
    );
  }

  return (
    <View style={{ gap: 8 }}>
      <Pressable
        testID="settings-export-button"
        style={styles.button}
        disabled={start.isPending || poll.isPending}
        onPress={() => (jobId ? poll.mutate(jobId) : start.mutate())}
      >
        {start.isPending || poll.isPending ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonLabel}>{jobId ? "Check export status" : "Export my data"}</Text>
        )}
      </Pressable>
      {start.isError ? <Text style={styles.error}>{describeApiError(start.error)}</Text> : null}
      {poll.isError ? <Text style={styles.error}>{describeApiError(poll.error)}</Text> : null}
    </View>
  );
}

function DeleteAccountFlow({ userId, onDeleted }: { userId: string; onDeleted: () => void }) {
  const [phrase, setPhrase] = useState("");
  const remove = useMutation({
    mutationFn: () => deleteAccount(userId, phrase),
    onSuccess: () => {
      Alert.alert(
        "Account deleted",
        "Your account has been deactivated and will be permanently removed within 72 hours.",
      );
      onDeleted();
    },
  });

  return (
    <View style={{ gap: 8 }}>
      <Text style={styles.hint}>
        Type "{REQUIRED_CONFIRMATION_PHRASE}" to confirm.
      </Text>
      <TextInput
        style={styles.input}
        value={phrase}
        onChangeText={setPhrase}
        placeholder={REQUIRED_CONFIRMATION_PHRASE}
        autoCapitalize="characters"
        testID="settings-delete-confirm-input"
      />
      <Pressable
        style={[styles.button, styles.dangerButton, phrase !== REQUIRED_CONFIRMATION_PHRASE && styles.buttonDisabled]}
        disabled={phrase !== REQUIRED_CONFIRMATION_PHRASE || remove.isPending}
        accessibilityRole="button"
        accessibilityState={{
          disabled: phrase !== REQUIRED_CONFIRMATION_PHRASE || remove.isPending,
        }}
        onPress={() => remove.mutate()}
        testID="settings-delete-confirm-button"
      >
        {remove.isPending ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonLabel}>Delete my account</Text>
        )}
      </Pressable>
      {remove.isError ? <Text style={styles.error}>{describeApiError(remove.error)}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, gap: 24 },
  header: { fontSize: 24, fontWeight: "600" },
  section: { gap: 10, borderTopWidth: 1, borderTopColor: "#EEE", paddingTop: 16 },
  sectionTitle: { fontSize: 16, fontWeight: "700" },
  sectionBody: { color: "#6B6B6B", fontSize: 13 },
  hint: { fontSize: 12, color: "#6B6B6B" },
  input: {
    borderWidth: 1,
    borderColor: "#E5E5E5",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  button: {
    backgroundColor: "#4A6FA5",
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: "center",
  },
  buttonDisabled: { opacity: 0.4 },
  dangerButton: { backgroundColor: "#C0392B" },
  buttonLabel: { color: "#fff", fontWeight: "600" },
  error: { color: "#C0392B", fontSize: 12 },
  linkButton: { paddingVertical: 4 },
  linkButtonText: { color: "#4A6FA5", fontWeight: "600" },
});
