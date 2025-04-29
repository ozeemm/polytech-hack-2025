import './Loader.css'

export default function Loader(props){
    if(props.isLoading)
        return(
            <div className='panel'>
                <div className="loader"></div>
            </div>
        )
}