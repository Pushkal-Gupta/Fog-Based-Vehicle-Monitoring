import { Button } from '@/components/ui/button'
import { ButtonGroup } from '@/components/ui/button-group'

import { createFileRoute, Link } from '@tanstack/react-router'
import { ArrowLeftIcon, BadgePlus } from 'lucide-react'
import { Arrow } from 'node_modules/@base-ui/react/esm/autocomplete/index.parts'

export const Route = createFileRoute('/_authenticated/claim-vehicle')({
  component: ClaimVehiclePage,
})

function ClaimVehiclePage() {
  return (
    <div className='w-full flex justify-center'>
      <div className='w-7/12 border justify-center p-5 gap-10'>
        <h1 className='text-center'>Claim a vehicle</h1>
        <div className='gap-10 flex'>
          <div>
            <Link to='/'>
              <ButtonGroup>
                <Button variant={'outline'}><ArrowLeftIcon /></Button>
                <Button variant={'outline'}>Go Back Home</Button>
              </ButtonGroup>
            </Link>
          </div>
          <br></br>
          <div className=' border'>
            <BadgePlus />
          </div>
        </div>



      </div>
    </div>

  )
}
