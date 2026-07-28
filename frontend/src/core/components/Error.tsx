import React from 'react'

type Props = {
  error : string;
}

const Error = ({error = 'Something went wrong'}: Props) => {
  return (
    <div>{error}</div>
  )
}

export default Error