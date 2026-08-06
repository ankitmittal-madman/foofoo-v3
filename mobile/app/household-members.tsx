import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { router } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  acceptHouseholdInvite,
  createHouseholdInvite,
  leaveHousehold,
  listHouseholdAccess,
  listMyHouseholds,
  type HouseholdRole,
  type InvitableRole,
  updateHouseholdMember,
} from "@/api/householdAccess";
import { describeApiError } from "@/api/errorMessages";
import { useSession } from "@/auth/SessionContext";
import {
  clearActiveHousehold,
  getActiveHouseholdId,
  setActiveHouseholdId,
} from "@/household/activeHousehold";
import { FButton, palette } from "@/ui/foofoo";

const INVITABLE_ROLES: InvitableRole[] = ["planner", "cook", "member", "viewer"];

export default function HouseholdMembers() {
  const { session } = useSession();
  const queryClient = useQueryClient();
  const [activeId, setActiveId] = useState<string | null>(null);
  const [inviteRole, setInviteRole] = useState<InvitableRole>("member");
  const [inviteToken, setInviteToken] = useState("");
  const [acceptToken, setAcceptToken] = useState("");

  const households = useQuery({ queryKey: ["households"], queryFn: listMyHouseholds });
  const access = useQuery({
    queryKey: ["household-access", activeId],
    queryFn: () => listHouseholdAccess(activeId!),
    enabled: Boolean(activeId),
  });

  useEffect(() => {
    getActiveHouseholdId().then(setActiveId).catch(() => {});
    // This effect runs when the list of households changes or on initial load.
    // It ensures a valid household is always selected if one exists.
    if (households.isSuccess) {
      const householdList = households.data?.households ?? [];
      if (householdList.length === 0) return;

      const currentIdIsValid = activeId && householdList.some((h) => h.household_id === activeId);

      if (!currentIdIsValid) {
        const nextId = householdList[0].household_id;
        selectHousehold(nextId).catch(() => {});
      }
    }
  }, [households.isSuccess, households.data, activeId]);

  async function selectHousehold(householdId: string) {
    await setActiveHouseholdId(householdId);
    setActiveId(householdId);
    queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== "households" });
  }

  const createInvite = useMutation({
    mutationFn: () => createHouseholdInvite(activeId!, inviteRole),
    onSuccess: (result) => {
      setInviteToken(result.token);
      queryClient.invalidateQueries({ queryKey: ["household-access", activeId] });
    },
  });
  const acceptInvite = useMutation({
    mutationFn: () => acceptHouseholdInvite(acceptToken),
    onSuccess: async (result) => {
      setAcceptToken("");
      await selectHousehold(result.household_id);
      await queryClient.invalidateQueries({ queryKey: ["households"] });
    },
  });
  const mutateMember = useMutation({
    mutationFn: (input: {
      action: "change_role" | "revoke" | "transfer_owner";
      userId: string;
      role?: InvitableRole;
    }) => updateHouseholdMember(activeId!, input.action, input.userId, input.role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["household-access", activeId] });
      queryClient.invalidateQueries({ queryKey: ["households"] });
    },
  });
  const leave = useMutation({
    mutationFn: () => leaveHousehold(activeId!),
    onSuccess: async () => {
      await clearActiveHousehold();
      setActiveId(null);
      await queryClient.invalidateQueries({ queryKey: ["households"] });
    },
  });

  const owner = access.data?.caller_role === "owner";
  const error = households.error ?? access.error ?? createInvite.error ?? acceptInvite.error ??
    mutateMember.error ?? leave.error;

  return (
    <ScrollView testID="household-members-screen" style={styles.screen} contentContainerStyle={styles.page}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()}><Text style={styles.back}>‹</Text></Pressable>
        <Text style={styles.title}>Household access</Text><View style={{ width: 24 }} />
      </View>
      <Text style={styles.intro}>
        Choose the household whose plans you want to see. Roles control what each account can
        change; food participants without accounts remain separate.
      </Text>

      <Text style={styles.heading}>Your households</Text>
      {households.isLoading ? <ActivityIndicator /> : null}
      <View style={styles.chips}>
        {(households.data?.households ?? []).map((row) => (
          <Pressable
            key={row.household_id}
            testID={`household-select-${row.household_id}`}
            onPress={() => selectHousehold(row.household_id)}
            style={[styles.householdChip, activeId === row.household_id && styles.householdChipActive]}
          >
            <Text style={activeId === row.household_id ? styles.activeText : styles.chipText}>
              {row.name} · {row.role}
            </Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.card}>
        <Text style={styles.heading}>Join with an invite</Text>
        <TextInput
          testID="household-invite-token-input"
          style={styles.input}
          value={acceptToken}
          onChangeText={setAcceptToken}
          autoCapitalize="none"
          placeholder="Paste invitation token"
        />
        <FButton
          label={acceptInvite.isPending ? "Joining…" : "Join household"}
          disabled={acceptToken.trim().length < 32 || acceptInvite.isPending}
          onPress={() => acceptInvite.mutate()}
        />
      </View>

      {access.isLoading ? <ActivityIndicator /> : null}
      {access.data ? (
        <View style={styles.card}>
          <Text style={styles.heading}>Members</Text>
          <Text style={styles.roleNote}>Your role: {access.data.caller_role}</Text>
          {access.data.memberships.filter((row) => row.status === "active").map((member) => (
            <View key={member.user_id} style={styles.memberRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.memberName}>
                  {member.user_id === session?.user.id ? "You" : shortId(member.user_id)}
                </Text>
                <Text style={styles.roleNote}>{member.role_code}</Text>
              </View>
              {owner && member.role_code !== "owner" ? (
                <View style={styles.memberActions}>
                  <RolePicker
                    value={member.role_code as InvitableRole}
                    onChange={(role) => mutateMember.mutate({
                      action: "change_role",
                      userId: member.user_id,
                      role,
                    })}
                  />
                  <Pressable
                    testID={`household-transfer-${member.user_id}`}
                    onPress={() => confirm(
                      "Transfer ownership?",
                      "You will become a planner and this member will control household access.",
                      () => mutateMember.mutate({ action: "transfer_owner", userId: member.user_id }),
                    )}
                  ><Text style={styles.link}>Make owner</Text></Pressable>
                  <Pressable
                    testID={`household-revoke-${member.user_id}`}
                    onPress={() => confirm(
                      "Remove member?",
                      "Their past membership history will be retained.",
                      () => mutateMember.mutate({ action: "revoke", userId: member.user_id }),
                    )}
                  ><Text style={styles.danger}>Remove</Text></Pressable>
                </View>
              ) : null}
            </View>
          ))}
        </View>
      ) : null}

      {owner && activeId ? (
        <View style={styles.card}>
          <Text style={styles.heading}>Invite another account</Text>
          <RolePicker value={inviteRole} onChange={setInviteRole} />
          <FButton
            label={createInvite.isPending ? "Creating…" : "Create secure invite"}
            disabled={createInvite.isPending}
            onPress={() => createInvite.mutate()}
          />
          {inviteToken ? (
            <View style={styles.tokenBox}>
              <Text selectable style={styles.token}>{inviteToken}</Text>
              <Pressable
                testID="household-share-invite"
                onPress={() => Share.share({
                  message: `Join my Foofoo household with this one-time token:\n${inviteToken}`,
                })}
              ><Text style={styles.link}>Share invitation</Text></Pressable>
              <Text style={styles.tokenWarning}>Shown once. Foofoo stores only its secure hash.</Text>
            </View>
          ) : null}
        </View>
      ) : null}

      {access.data && !owner ? (
        <Pressable
          testID="household-leave"
          style={styles.leaveButton}
          onPress={() => confirm(
            "Leave household?",
            "You will need a new invite to rejoin.",
            () => leave.mutate(),
          )}
        ><Text style={styles.danger}>Leave this household</Text></Pressable>
      ) : null}
      {error ? <Text style={styles.error}>{describeApiError(error)}</Text> : null}
    </ScrollView>
  );
}

function shortId(value: string) {
  return `Member ${value.slice(0, 6)}`;
}

function confirm(title: string, message: string, action: () => void) {
  Alert.alert(title, message, [{ text: "Cancel", style: "cancel" }, { text: "Continue", onPress: action }]);
}

function RolePicker({ value, onChange }: { value: InvitableRole; onChange: (role: InvitableRole) => void }) {
  return <View style={styles.roles}>{INVITABLE_ROLES.map((role) => (
    <Pressable
      key={role}
      testID={`household-role-${role}`}
      onPress={() => onChange(role)}
      style={[styles.roleChip, value === role && styles.roleChipActive]}
    ><Text style={value === role ? styles.activeText : styles.chipText}>{role}</Text></Pressable>
  ))}</View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.bg },
  page: { padding: 18, paddingBottom: 80, gap: 14 },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  back: { fontSize: 34, color: palette.ink },
  title: { fontSize: 19, fontWeight: "800", color: palette.ink },
  intro: { color: palette.muted, lineHeight: 20 },
  heading: { fontSize: 16, fontWeight: "800", color: palette.ink },
  card: { padding: 15, gap: 12, borderRadius: 16, backgroundColor: palette.surface, borderWidth: 1, borderColor: palette.line },
  chips: { gap: 8 },
  householdChip: { padding: 12, borderRadius: 12, borderWidth: 1, borderColor: palette.line, backgroundColor: palette.surface },
  householdChipActive: { backgroundColor: palette.purple, borderColor: palette.purple },
  chipText: { color: palette.ink, fontSize: 12, fontWeight: "600" },
  activeText: { color: "white", fontSize: 11, fontWeight: "700" },
  input: { borderWidth: 1, borderColor: palette.line, backgroundColor: "white", borderRadius: 10, paddingHorizontal: 12, paddingVertical: 11 },
  roleNote: { color: palette.muted, fontSize: 11 },
  memberRow: { flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 10, borderTopWidth: 1, borderTopColor: palette.line },
  memberName: { color: palette.ink, fontWeight: "700" },
  memberActions: { alignItems: "flex-end", gap: 6, maxWidth: "65%" },
  roles: { flexDirection: "row", flexWrap: "wrap", gap: 5 },
  roleChip: { paddingHorizontal: 8, paddingVertical: 6, borderRadius: 8, backgroundColor: palette.beige },
  roleChipActive: { backgroundColor: palette.purple },
  link: { color: palette.purple, fontWeight: "700", fontSize: 12 },
  danger: { color: palette.red, fontWeight: "700", fontSize: 12 },
  tokenBox: { gap: 8, padding: 10, borderRadius: 10, backgroundColor: palette.purpleSoft },
  token: { fontSize: 10, color: palette.ink },
  tokenWarning: { color: palette.muted, fontSize: 10 },
  leaveButton: { padding: 14, alignItems: "center" },
  error: { color: palette.red, fontSize: 12 },
});
