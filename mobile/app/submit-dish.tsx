import { useMutation } from "@tanstack/react-query";
import { router } from "expo-router";
import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { describeApiError } from "@/api/errorMessages";
import { submitUnknownDish } from "@/api/dishOntology";

function commaList(value: string): string[] {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

/** Mobile intake for dishes missing from the governed catalogue. */
export default function SubmitDishScreen() {
  const [name, setName] = useState("");
  const [aliases, setAliases] = useState("");
  const [ingredients, setIngredients] = useState("");
  const [cuisine, setCuisine] = useState("");
  const [region, setRegion] = useState("");
  const [notes, setNotes] = useState("");
  const [mealSlots, setMealSlots] = useState("lunch, dinner");
  const [cookTime, setCookTime] = useState("30");
  const mutation = useMutation({
    mutationFn: () =>
      submitUnknownDish(name.trim(), {
        aliases: commaList(aliases),
        ingredients: commaList(ingredients),
        cuisine: cuisine.trim() || undefined,
        region: region.trim() || undefined,
        meal_slots: commaList(mealSlots).map((item) => item.toLowerCase()),
        cook_time_minutes: Number(cookTime) || 30,
        notes: notes.trim() || undefined,
      }),
  });

  if (mutation.data) {
    return (
      <View testID="dish-submission-success" style={styles.container}>
        <Text style={styles.title}>Dish received</Text>
        <Text style={styles.body}>
          {mutation.data.submission.entered_name}{" "}
          is being checked against food references and our safety rules. It will only enter
          recommendations after it is promoted to the catalogue.
        </Text>
        <Text style={styles.status}>
          Status: {mutation.data.research.next_status.replaceAll("_", " ")}
        </Text>
        <Pressable style={styles.primary} onPress={() => router.back()}>
          <Text style={styles.primaryText}>Back to search</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView
      testID="submit-dish-screen"
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Text style={styles.title}>Add a missing dish</Text>
      <Text style={styles.body}>
        Share what you know. Name is required; extra details help us match it safely.
      </Text>
      <Field
        label="Dish name *"
        value={name}
        onChangeText={setName}
        placeholder="e.g. Kanda poha"
        testID="dish-name"
      />
      <Field
        label="Other or regional names"
        value={aliases}
        onChangeText={setAliases}
        placeholder="Comma-separated"
      />
      <Field
        label="Main ingredients"
        value={ingredients}
        onChangeText={setIngredients}
        placeholder="Comma-separated"
      />
      <Field
        label="Cuisine"
        value={cuisine}
        onChangeText={setCuisine}
        placeholder="e.g. Maharashtrian"
      />
      <Field label="Region" value={region} onChangeText={setRegion} placeholder="State or region" />
      <Field
        label="Meal slots"
        value={mealSlots}
        onChangeText={setMealSlots}
        placeholder="breakfast, lunch, dinner, snack"
      />
      <Field
        label="Cook time (minutes)"
        value={cookTime}
        onChangeText={setCookTime}
        placeholder="30"
      />
      <Field
        label="Anything else"
        value={notes}
        onChangeText={setNotes}
        placeholder="Preparation, meal, dietary notes"
        multiline
      />
      {mutation.isError
        ? <Text style={styles.error}>{describeApiError(mutation.error)}</Text>
        : null}
      <Pressable
        testID="dish-submit"
        disabled={name.trim().length < 2 || mutation.isPending}
        style={[styles.primary, (name.trim().length < 2 || mutation.isPending) && styles.disabled]}
        onPress={() => mutation.mutate()}
      >
        <Text style={styles.primaryText}>{mutation.isPending ? "Checking…" : "Submit dish"}</Text>
      </Pressable>
      <Pressable onPress={() => router.back()}>
        <Text style={styles.cancel}>Cancel</Text>
      </Pressable>
    </ScrollView>
  );
}

function Field(props: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder: string;
  multiline?: boolean;
  testID?: string;
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{props.label}</Text>
      <TextInput
        testID={props.testID}
        value={props.value}
        onChangeText={props.onChangeText}
        placeholder={props.placeholder}
        multiline={props.multiline}
        style={[styles.input, props.multiline && styles.multiline]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 24, gap: 14, justifyContent: "center" },
  title: { fontSize: 26, fontWeight: "700" },
  body: { color: "#555", fontSize: 16, lineHeight: 23 },
  field: { gap: 5 },
  label: { fontWeight: "600" },
  input: {
    borderWidth: 1,
    borderColor: "#BBB",
    borderRadius: 9,
    padding: 11,
    backgroundColor: "white",
  },
  multiline: { minHeight: 82, textAlignVertical: "top" },
  primary: { backgroundColor: "#1F7A3F", padding: 13, borderRadius: 9, alignItems: "center" },
  primaryText: { color: "white", fontWeight: "700" },
  disabled: { opacity: 0.45 },
  cancel: { color: "#1F7A3F", textAlign: "center", padding: 8 },
  error: { color: "#C0392B" },
  status: { fontWeight: "600" },
});
