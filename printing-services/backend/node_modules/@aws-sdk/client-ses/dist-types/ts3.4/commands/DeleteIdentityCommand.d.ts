import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  DeleteIdentityRequest,
  DeleteIdentityResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DeleteIdentityCommandInput extends DeleteIdentityRequest {}
export interface DeleteIdentityCommandOutput
  extends DeleteIdentityResponse,
    __MetadataBearer {}
declare const DeleteIdentityCommand_base: {
  new (
    input: DeleteIdentityCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteIdentityCommandInput,
    DeleteIdentityCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DeleteIdentityCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteIdentityCommandInput,
    DeleteIdentityCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DeleteIdentityCommand extends DeleteIdentityCommand_base {
  protected static __types: {
    api: {
      input: DeleteIdentityRequest;
      output: {};
    };
    sdk: {
      input: DeleteIdentityCommandInput;
      output: DeleteIdentityCommandOutput;
    };
  };
}
