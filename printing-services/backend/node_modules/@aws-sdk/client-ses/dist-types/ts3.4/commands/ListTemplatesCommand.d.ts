import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  ListTemplatesRequest,
  ListTemplatesResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface ListTemplatesCommandInput extends ListTemplatesRequest {}
export interface ListTemplatesCommandOutput
  extends ListTemplatesResponse,
    __MetadataBearer {}
declare const ListTemplatesCommand_base: {
  new (
    input: ListTemplatesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ListTemplatesCommandInput,
    ListTemplatesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [ListTemplatesCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    ListTemplatesCommandInput,
    ListTemplatesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class ListTemplatesCommand extends ListTemplatesCommand_base {
  protected static __types: {
    api: {
      input: ListTemplatesRequest;
      output: ListTemplatesResponse;
    };
    sdk: {
      input: ListTemplatesCommandInput;
      output: ListTemplatesCommandOutput;
    };
  };
}
