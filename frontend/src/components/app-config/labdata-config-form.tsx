import { useUserConfig } from "@/core/config/config";
import { FormField, FormItem, FormLabel } from "../ui/form";
import { Input } from "../ui/input";
import { Switch } from "../ui/switch";

export const LabdataConfigForm: React.FC = () => {
  const [userConfig, setUserConfig] = useUserConfig();

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Labdata Configuration</h2>
      
      <FormField>
        <FormItem>
          <FormLabel>Authentication Method</FormLabel>
          <select
            value={userConfig.labdata.auth_method}
            onChange={(e) =>
              setUserConfig({
                ...userConfig,
                labdata: {
                  ...userConfig.labdata,
                  auth_method: e.target.value,
                },
              })
            }
          >
            <option value="oauth">OAuth</option>
            <option value="token">API Token</option>
          </select>
        </FormItem>
      </FormField>

      <FormField>
        <FormItem>
          <FormLabel>Credentials Path</FormLabel>
          <Input
            value={userConfig.labdata.credentials_path}
            onChange={(e) =>
              setUserConfig({
                ...userConfig,
                labdata: {
                  ...userConfig.labdata,
                  credentials_path: e.target.value,
                },
              })
            }
          />
        </FormItem>
      </FormField>

      <FormField>
        <FormItem>
          <FormLabel>Auto-connect</FormLabel>
          <Switch
            checked={userConfig.labdata.auto_connect}
            onCheckedChange={(checked) =>
              setUserConfig({
                ...userConfig,
                labdata: {
                  ...userConfig.labdata,
                  auto_connect: checked,
                },
              })
            }
          />
        </FormItem>
      </FormField>
    </div>
  );
};