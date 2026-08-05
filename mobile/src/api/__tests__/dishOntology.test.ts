import { apiPost } from "../client";
import { getDishOntologyRecord, submitUnknownDish } from "../dishOntology";

jest.mock("../client", () => ({ apiPost: jest.fn() }));

const mockedPost = apiPost as jest.MockedFunction<typeof apiPost>;

describe("dish ontology client", () => {
  beforeEach(() => mockedPost.mockReset());

  it("submits unknown dishes only through the staging action", async () => {
    mockedPost.mockResolvedValueOnce({ kind: "dish_submission" });
    await submitUnknownDish("Dal Dhokli", { region: "Gujarat", ingredients: ["Tuvar Dal"] });
    expect(mockedPost).toHaveBeenCalledWith("/v1/dish-ontology", {
      action: "submit",
      name: "Dal Dhokli",
      metadata: { region: "Gujarat", ingredients: ["Tuvar Dal"] },
    });
  });

  it("requests the governed ontology read model by canonical ID", async () => {
    mockedPost.mockResolvedValueOnce({ kind: "dish_ontology_record", record: {} });
    await getDishOntologyRecord({ dishId: "11111111-1111-4111-8111-111111111111" });
    expect(mockedPost).toHaveBeenCalledWith("/v1/dish-ontology", {
      action: "ontology_record",
      dish_id: "11111111-1111-4111-8111-111111111111",
      name: undefined,
    });
  });
});
