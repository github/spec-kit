import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  DeleteIdentityPolicyRequest,
  DeleteIdentityPolicyResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DeleteIdentityPolicyCommandInput
  extends DeleteIdentityPolicyRequest {}
export interface DeleteIdentityPolicyCommandOutput
  extends DeleteIdentityPolicyResponse,
    __MetadataBearer {}
declare const DeleteIdentityPolicyCommand_base: {
  new (
    input: DeleteIdentityPolicyCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteIdentityPolicyCommandInput,
    DeleteIdentityPolicyCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DeleteIdentityPolicyCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteIdentityPolicyCommandInput,
    DeleteIdentityPolicyCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DeleteIdentityPolicyCommand extends DeleteIdentityPolicyCommand_base {
  protected static __types: {
    api: {
      input: DeleteIdentityPolicyRequest;
      output: {};
    };
    sdk: {
      input: DeleteIdentityPolicyCommandInput;
      output: DeleteIdentityPolicyCommandOutput;
    };
  };
}
