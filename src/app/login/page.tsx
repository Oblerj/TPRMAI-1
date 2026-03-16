import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Shield } from 'lucide-react'
import { handleOIDCSignIn } from './actions'

export default function LoginPage() {

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 rounded-full bg-blue-100">
              <Shield className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <CardTitle className="text-2xl">AI TPRM System</CardTitle>
          <CardDescription>
            Third Party Risk Management for Sleep Number
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form action={handleOIDCSignIn} className="space-y-4">
            {/* OIDC Sign In */}
            <Button
              type="submit"
              variant="default"
              className="w-full"
            >
              Sign In
            </Button>

            <p className="text-xs text-gray-500 text-center mt-4">
              Use your Sleep Number credentials to access the AI TPRM system.
            </p>
          </form>

          <p className="text-xs text-gray-500 text-center mt-6">
            Protected by Sleep Number Information Security
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
